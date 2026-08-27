from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import torch
from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import ManagerTermBase, SceneEntityCfg
from isaaclab.sensors import ContactSensor

try:
    from isaaclab.utils.math import quat_apply, quat_apply_inverse
except ImportError:
    from isaaclab.utils.math import quat_rotate as quat_apply
    from isaaclab.utils.math import quat_rotate_inverse as quat_apply_inverse

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def energy(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    asset: Articulation = env.scene[asset_cfg.name]
    joint_vel = asset.data.joint_vel[:, asset_cfg.joint_ids]
    applied_torque = asset.data.applied_torque[:, asset_cfg.joint_ids]
    return torch.sum(torch.abs(joint_vel) * torch.abs(applied_torque), dim=-1)


def stand_still(
    env: ManagerBasedRLEnv,
    command_name: str = "base_velocity",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    asset: Articulation = env.scene[asset_cfg.name]
    joint_error = torch.sum(
        torch.abs(asset.data.joint_pos - asset.data.default_joint_pos), dim=1
    )
    command_norm = torch.linalg.vector_norm(
        env.command_manager.get_command(command_name), dim=1
    )
    return joint_error * (command_norm < 0.1)


def track_ang_vel_z_world_exp(
    env: ManagerBasedRLEnv,
    std: float,
    command_name: str,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    asset: RigidObject = env.scene[asset_cfg.name]
    error = torch.square(
        env.command_manager.get_command(command_name)[:, 2]
        - asset.data.root_ang_vel_w[:, 2]
    )
    return torch.exp(-error / std**2)


def lin_vel_z_world_l2(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    asset: RigidObject = env.scene[asset_cfg.name]
    return torch.square(asset.data.root_lin_vel_w[:, 2])


def ang_vel_xy_world_l2(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    asset: RigidObject = env.scene[asset_cfg.name]
    return torch.sum(torch.square(asset.data.root_ang_vel_w[:, :2]), dim=1)


def desired_orientation_l2(
    env: ManagerBasedRLEnv,
    desired_gravity: list[float],
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    asset: RigidObject = env.scene[asset_cfg.name]
    target = torch.as_tensor(
        desired_gravity,
        device=env.device,
        dtype=asset.data.projected_gravity_b.dtype,
    )
    target = target / torch.linalg.vector_norm(target)
    return torch.sum(torch.square(asset.data.projected_gravity_b - target), dim=-1)


def feet_flat(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg,
    asset_cfg: SceneEntityCfg,
    flat_std: float = 0.2,
    local_normal: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> torch.Tensor:
    contact_sensor: ContactSensor = env.scene.sensors[sensor_cfg.name]
    asset: Articulation = env.scene[asset_cfg.name]
    contact = contact_sensor.data.current_contact_time[:, sensor_cfg.body_ids] > 0.0
    foot_quat = asset.data.body_quat_w[:, asset_cfg.body_ids]

    normal_b = torch.as_tensor(
        local_normal,
        device=env.device,
        dtype=foot_quat.dtype,
    ).view(1, 1, 3)
    foot_normal_w = quat_apply(
        foot_quat,
        normal_b.expand(foot_quat.shape[0], foot_quat.shape[1], -1),
    )
    alignment = foot_normal_w[..., 2].clamp(-1.0, 1.0)
    flat_score = torch.exp(-torch.square((1.0 - alignment) / flat_std))
    contact_f = contact.to(flat_score.dtype)
    return torch.sum(flat_score * contact_f, dim=1) / torch.sum(
        contact_f, dim=1
    ).clamp_min(1.0)


def feet_lateral_distance_l2(
    env: ManagerBasedRLEnv,
    minimum_distance: float,
    asset_cfg: SceneEntityCfg,
) -> torch.Tensor:
    asset: Articulation = env.scene[asset_cfg.name]
    foot_pos_w = asset.data.body_pos_w[:, asset_cfg.body_ids]
    if foot_pos_w.shape[1] != 2:
        raise ValueError("feet_lateral_distance_l2 requires left and right foot bodies.")

    left_to_right_w = foot_pos_w[:, 0] - foot_pos_w[:, 1]
    left_to_right_b = quat_apply_inverse(asset.data.root_quat_w, left_to_right_w)
    shortfall = torch.clamp(minimum_distance - left_to_right_b[:, 1], min=0.0)
    return torch.square(shortfall)


def foot_clearance_weighted_by_velocity(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg,
    target_height: float,
) -> torch.Tensor:
    asset: RigidObject = env.scene[asset_cfg.name]
    foot_height = (
        asset.data.body_pos_w[:, asset_cfg.body_ids, 2]
        - env.scene.env_origins[:, 2].unsqueeze(1)
    )
    height_error = torch.abs(foot_height - target_height)
    foot_speed_xy = torch.linalg.vector_norm(
        asset.data.body_lin_vel_w[:, asset_cfg.body_ids, :2], dim=-1
    )
    return torch.sum(height_error * foot_speed_xy, dim=1)


class ActionSecondOrderPenalty(ManagerTermBase):
    """Penalize the second finite difference of policy actions."""

    def __init__(self, cfg, env: ManagerBasedRLEnv):
        super().__init__(cfg, env)
        self._previous_previous_action = torch.zeros_like(env.action_manager.action)

    def reset(self, env_ids: Sequence[int] | None = None) -> None:
        if env_ids is None:
            self._previous_previous_action.zero_()
        else:
            self._previous_previous_action[env_ids] = 0.0

    def __call__(self, env: ManagerBasedRLEnv) -> torch.Tensor:
        action = env.action_manager.action
        previous_action = env.action_manager.prev_action
        second_difference = (
            action - 2.0 * previous_action + self._previous_previous_action
        )
        penalty = torch.sum(torch.square(second_difference), dim=1)
        penalty = penalty.masked_fill(env.episode_length_buf <= 1, 0.0)
        self._previous_previous_action.copy_(previous_action)
        return penalty
