from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from isaaclab.assets import RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def bad_orientation_from_desired_gravity(
    env: ManagerBasedRLEnv,
    limit_angle: float,
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
    cosine = torch.sum(asset.data.projected_gravity_b * target, dim=-1).clamp(-1.0, 1.0)
    return torch.acos(cosine) > limit_angle

