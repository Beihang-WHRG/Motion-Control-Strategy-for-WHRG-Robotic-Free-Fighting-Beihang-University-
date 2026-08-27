"""Train the boxing locomotion task with RSL-RL."""

import argparse
import inspect
import os
import shutil
import sys
from datetime import datetime

import argcomplete
from isaaclab.app import AppLauncher

import cli_args


TASK_ID = "Unitree-G1-29dof-Boxing"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--video", action="store_true", default=False)
parser.add_argument("--video_length", type=int, default=200)
parser.add_argument("--video_interval", type=int, default=2000)
parser.add_argument("--num_envs", type=int, default=None)
parser.add_argument("--task", type=str, default=TASK_ID)
parser.add_argument("--seed", type=int, default=None)
parser.add_argument("--max_iterations", type=int, default=None)
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
argcomplete.autocomplete(parser)
args_cli, hydra_args = parser.parse_known_args()

if args_cli.video:
    args_cli.enable_cameras = True
sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym
from rsl_rl.runners import OnPolicyRunner

import isaaclab_tasks  # noqa: F401, E402
import boxing  # noqa: F401, E402
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.utils.dict import print_dict
from isaaclab.utils.io import dump_yaml
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlVecEnvWrapper
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config


@hydra_task_config(args_cli.task, "rsl_rl_cfg_entry_point")
def main(
    env_cfg: ManagerBasedRLEnvCfg,
    agent_cfg: RslRlOnPolicyRunnerCfg,
) -> None:
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    if args_cli.num_envs is not None:
        env_cfg.scene.num_envs = args_cli.num_envs
    if args_cli.max_iterations is not None:
        agent_cfg.max_iterations = args_cli.max_iterations

    env_cfg.seed = agent_cfg.seed
    if args_cli.device is not None:
        env_cfg.sim.device = args_cli.device

    log_root = os.path.abspath(
        os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
    )
    run_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if agent_cfg.run_name:
        run_name += f"_{agent_cfg.run_name}"
    log_dir = os.path.join(log_root, run_name)
    print(f"[INFO] Logging experiment in: {log_dir}")

    resume_path = None
    direct_checkpoint = (
        os.path.abspath(os.path.expanduser(args_cli.checkpoint))
        if args_cli.checkpoint is not None
        else None
    )
    if direct_checkpoint is not None and os.path.isfile(direct_checkpoint):
        resume_path = direct_checkpoint
    elif agent_cfg.resume:
        resume_path = get_checkpoint_path(
            log_root,
            agent_cfg.load_run,
            agent_cfg.load_checkpoint,
        )
    elif direct_checkpoint is not None:
        raise FileNotFoundError(f"Checkpoint not found: {direct_checkpoint}")

    env = gym.make(
        args_cli.task,
        cfg=env_cfg,
        render_mode="rgb_array" if args_cli.video else None,
    )
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "train"),
            "step_trigger": lambda step: step % args_cli.video_interval == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = OnPolicyRunner(
        env,
        agent_cfg.to_dict(),
        log_dir=log_dir,
        device=agent_cfg.device,
    )
    runner.add_git_repo_to_log(__file__)
    if resume_path is not None:
        print(f"[INFO] Loading checkpoint: {resume_path}")
        runner.load(resume_path)

    dump_yaml(os.path.join(log_dir, "params", "env.yaml"), env_cfg)
    dump_yaml(os.path.join(log_dir, "params", "agent.yaml"), agent_cfg)
    shutil.copy(
        inspect.getfile(env_cfg.__class__),
        os.path.join(log_dir, "params", "env_cfg.py"),
    )
    runner.learn(
        num_learning_iterations=agent_cfg.max_iterations,
        init_at_random_ep_len=True,
    )
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
