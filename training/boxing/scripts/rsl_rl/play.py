"""Run a trained boxing locomotion checkpoint."""

import argparse
import os

from isaaclab.app import AppLauncher

import cli_args


TASK_ID = "Unitree-G1-29dof-Boxing"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--task", type=str, default=TASK_ID)
parser.add_argument("--num_envs", type=int, default=32)
parser.add_argument("--seed", type=int, default=None)
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym
import torch
from rsl_rl.runners import OnPolicyRunner

import isaaclab_tasks  # noqa: F401, E402
import boxing  # noqa: F401, E402
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg


def main() -> None:
    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        entry_point_key="play_env_cfg_entry_point",
    )
    agent_cfg = cli_args.parse_rsl_rl_cfg(args_cli.task, args_cli)
    log_root = os.path.abspath(
        os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
    )
    checkpoint = (
        os.path.abspath(args_cli.checkpoint)
        if args_cli.checkpoint
        else get_checkpoint_path(
            log_root,
            agent_cfg.load_run,
            agent_cfg.load_checkpoint,
        )
    )

    env = gym.make(args_cli.task, cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = OnPolicyRunner(
        env,
        agent_cfg.to_dict(),
        log_dir=None,
        device=agent_cfg.device,
    )
    runner.load(checkpoint)
    policy = runner.get_inference_policy(device=env.unwrapped.device)

    observations = env.get_observations()
    if isinstance(observations, tuple):
        observations = observations[0]
    while simulation_app.is_running():
        with torch.inference_mode():
            actions = policy(observations)
            observations = env.step(actions)[0]
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
