from isaaclab.assets import ArticulationCfg

from unitree_rl_lab.assets.robots.unitree import UNITREE_G1_29DOF_CFG


BOXING_ROBOT_CFG = UNITREE_G1_29DOF_CFG.replace(
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.684550849),
        rot=(0.998753785, 0.0, 0.049908686, 0.0),
        joint_pos={
            "left_hip_pitch_joint": -0.880403,
            "left_hip_roll_joint": 0.151306,
            "left_hip_yaw_joint": 0.001266,
            "left_knee_joint": 0.991313,
            "left_ankle_pitch_joint": -0.205753,
            "left_ankle_roll_joint": -0.085006,
            "right_hip_pitch_joint": -0.550518,
            "right_hip_roll_joint": -0.379054,
            "right_hip_yaw_joint": -0.308170,
            "right_knee_joint": 1.196097,
            "right_ankle_pitch_joint": -0.665226,
            "right_ankle_roll_joint": 0.098849,
            "waist_yaw_joint": 0.0,
            "waist_roll_joint": 0.0,
            "waist_pitch_joint": 0.0,
            "left_shoulder_pitch_joint": -0.728043,
            "left_shoulder_roll_joint": 0.108223,
            "left_shoulder_yaw_joint": -0.009257,
            "left_elbow_joint": 0.087854,
            "left_wrist_roll_joint": -0.125702,
            "left_wrist_pitch_joint": -0.066006,
            "left_wrist_yaw_joint": -0.024761,
            "right_shoulder_pitch_joint": -0.755417,
            "right_shoulder_roll_joint": -0.223752,
            "right_shoulder_yaw_joint": 0.240973,
            "right_elbow_joint": -0.088188,
            "right_wrist_roll_joint": 0.125702,
            "right_wrist_pitch_joint": -0.066006,
            "right_wrist_yaw_joint": 0.030802,
        },
        joint_vel={".*": 0.0},
    )
)

