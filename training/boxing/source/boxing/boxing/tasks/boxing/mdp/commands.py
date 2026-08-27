from __future__ import annotations

from collections.abc import Sequence
from dataclasses import MISSING

import torch
import isaaclab.utils.math as math_utils
from isaaclab.envs.mdp import UniformVelocityCommand, UniformVelocityCommandCfg
from isaaclab.utils import configclass


@configclass
class UniformLevelVelocityCommandCfg(UniformVelocityCommandCfg):
    limit_ranges: UniformVelocityCommandCfg.Ranges = MISSING


class RateLimitedUniformVelocityCommand(UniformVelocityCommand):
    """Uniform velocity command with a per-axis slew-rate limit."""

    cfg: RateLimitedUniformLevelVelocityCommandCfg

    def __init__(self, cfg: RateLimitedUniformLevelVelocityCommandCfg, env):
        super().__init__(cfg, env)
        if len(cfg.max_acceleration) != 3 or any(value <= 0.0 for value in cfg.max_acceleration):
            raise ValueError("max_acceleration must contain three positive values.")

        self.target_vel_command_b = torch.zeros_like(self.vel_command_b)
        self._max_command_step = (
            torch.tensor(cfg.max_acceleration, device=self.device, dtype=self.vel_command_b.dtype)
            * env.step_dt
        )

    def reset(self, env_ids: Sequence[int] | None = None) -> dict[str, float]:
        if env_ids is None:
            self.vel_command_b.zero_()
            self.target_vel_command_b.zero_()
            env_ids = torch.arange(self.num_envs, device=self.device)
        else:
            self.vel_command_b[env_ids] = 0.0
            self.target_vel_command_b[env_ids] = 0.0
        return super().reset(env_ids)

    def _resample_command(self, env_ids: Sequence[int]):
        random_values = torch.empty(len(env_ids), device=self.device)
        self.target_vel_command_b[env_ids, 0] = random_values.uniform_(*self.cfg.ranges.lin_vel_x)
        self.target_vel_command_b[env_ids, 1] = random_values.uniform_(*self.cfg.ranges.lin_vel_y)
        self.target_vel_command_b[env_ids, 2] = random_values.uniform_(*self.cfg.ranges.ang_vel_z)

        if self.cfg.heading_command:
            self.heading_target[env_ids] = random_values.uniform_(*self.cfg.ranges.heading)
            self.is_heading_env[env_ids] = random_values.uniform_(0.0, 1.0) <= self.cfg.rel_heading_envs
        self.is_standing_env[env_ids] = random_values.uniform_(0.0, 1.0) <= self.cfg.rel_standing_envs

    def _update_command(self):
        if self.cfg.heading_command:
            env_ids = self.is_heading_env.nonzero(as_tuple=False).flatten()
            heading_error = math_utils.wrap_to_pi(
                self.heading_target[env_ids] - self.robot.data.heading_w[env_ids]
            )
            self.target_vel_command_b[env_ids, 2] = torch.clip(
                self.cfg.heading_control_stiffness * heading_error,
                min=self.cfg.ranges.ang_vel_z[0],
                max=self.cfg.ranges.ang_vel_z[1],
            )

        standing_env_ids = self.is_standing_env.nonzero(as_tuple=False).flatten()
        self.target_vel_command_b[standing_env_ids] = 0.0
        command_delta = self.target_vel_command_b - self.vel_command_b
        self.vel_command_b += torch.clamp(
            command_delta,
            min=-self._max_command_step,
            max=self._max_command_step,
        )


@configclass
class RateLimitedUniformLevelVelocityCommandCfg(UniformLevelVelocityCommandCfg):
    class_type: type = RateLimitedUniformVelocityCommand
    max_acceleration: tuple[float, float, float] = MISSING
