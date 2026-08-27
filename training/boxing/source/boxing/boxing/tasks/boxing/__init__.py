import gymnasium as gym


TASK_ID = "Unitree-G1-29dof-Boxing"
PUSH_TASK_ID = "Unitree-G1-29dof-Boxing-Push"

gym.register(
    id=TASK_ID,
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.env_cfg:BoxingEnvCfg",
        "play_env_cfg_entry_point": f"{__name__}.env_cfg:BoxingPlayEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:BoxingPPORunnerCfg",
    },
)

gym.register(
    id=PUSH_TASK_ID,
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.push_env_cfg:BoxingPushEnvCfg",
        "play_env_cfg_entry_point": f"{__name__}.push_env_cfg:BoxingPushPlayEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:BoxingPPORunnerCfg",
    },
)

__all__ = ["PUSH_TASK_ID", "TASK_ID"]
