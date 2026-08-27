from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.utils import configclass

from . import mdp
from .env_cfg import BoxingEnvCfg, EventCfg


PUSH_VELOCITY_RANGE = {
    "x": (-0.30, 0.30),
    "y": (-0.25, 0.25),
    "z": (0.0, 0.0),
    "roll": (0.0, 0.0),
    "pitch": (0.0, 0.0),
    "yaw": (0.0, 0.0),
}


@configclass
class BoxingPushEventCfg(EventCfg):
    push_robot = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(8.0, 12.0),
        is_global_time=False,
        params={"velocity_range": PUSH_VELOCITY_RANGE},
    )


@configclass
class BoxingPushEnvCfg(BoxingEnvCfg):
    events: BoxingPushEventCfg = BoxingPushEventCfg()


@configclass
class BoxingPushPlayEnvCfg(BoxingPushEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 32
        self.commands.base_velocity.ranges = self.commands.base_velocity.limit_ranges
        self.commands.base_velocity.debug_vis = True
