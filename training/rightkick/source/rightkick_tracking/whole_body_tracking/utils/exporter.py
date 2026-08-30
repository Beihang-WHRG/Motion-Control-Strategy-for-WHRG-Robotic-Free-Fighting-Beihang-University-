# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import os

import onnx
import torch

from isaaclab.envs import ManagerBasedRLEnv
from isaaclab_rl.rsl_rl.exporter import _OnnxPolicyExporter

from whole_body_tracking.tasks.tracking.mdp import MotionCommand


# ============================================================================
# ONNX export
# ============================================================================


def export_motion_policy_as_onnx(
    env: ManagerBasedRLEnv,
    actor_critic: object,
    path: str,
    normalizer: object | None = None,
    filename: str = "policy.onnx",
    verbose: bool = False,
):
    """Export motion policy and reference motion data to ONNX."""

    if not os.path.exists(path):
        os.makedirs(
            path,
            exist_ok=True,
        )

    policy_exporter = _OnnxMotionPolicyExporter(
        env,
        actor_critic,
        normalizer,
        verbose,
    )

    policy_exporter.export(
        path,
        filename,
    )


# ============================================================================
# Motion policy exporter
# ============================================================================


class _OnnxMotionPolicyExporter(_OnnxPolicyExporter):
    """ONNX exporter including motion-reference outputs."""

    def __init__(
        self,
        env: ManagerBasedRLEnv,
        actor_critic,
        normalizer=None,
        verbose=False,
    ):
        super().__init__(
            actor_critic,
            normalizer,
            verbose,
        )

        cmd: MotionCommand = (
            env.command_manager.get_term(
                "motion"
            )
        )

        # --------------------------------------------------------------------
        # Store reference motion on CPU.
        # --------------------------------------------------------------------

        self.joint_pos = (
            cmd.motion.joint_pos
            .to("cpu")
        )

        self.joint_vel = (
            cmd.motion.joint_vel
            .to("cpu")
        )

        self.body_pos_w = (
            cmd.motion.body_pos_w
            .to("cpu")
        )

        self.body_quat_w = (
            cmd.motion.body_quat_w
            .to("cpu")
        )

        self.body_lin_vel_w = (
            cmd.motion.body_lin_vel_w
            .to("cpu")
        )

        self.body_ang_vel_w = (
            cmd.motion.body_ang_vel_w
            .to("cpu")
        )

        self.time_step_total = (
            self.joint_pos.shape[0]
        )

    def forward(
        self,
        x,
        time_step,
    ):
        """Forward pass used during ONNX tracing."""

        time_step_clamped = torch.clamp(
            time_step
            .long()
            .squeeze(-1),
            min=0,
            max=self.time_step_total - 1,
        )

        return (
            self.actor(
                self.normalizer(x)
            ),
            self.joint_pos[
                time_step_clamped
            ],
            self.joint_vel[
                time_step_clamped
            ],
            self.body_pos_w[
                time_step_clamped
            ],
            self.body_quat_w[
                time_step_clamped
            ],
            self.body_lin_vel_w[
                time_step_clamped
            ],
            self.body_ang_vel_w[
                time_step_clamped
            ],
        )

    def export(
        self,
        path,
        filename,
    ):
        """Export policy to ONNX."""

        self.to("cpu")

        obs = torch.zeros(
            1,
            self.actor[0].in_features,
        )

        time_step = torch.zeros(
            1,
            1,
        )

        onnx_path = os.path.join(
            path,
            filename,
        )

        torch.onnx.export(
            self,
            (
                obs,
                time_step,
            ),
            onnx_path,
            export_params=True,
            opset_version=11,
            verbose=self.verbose,
            input_names=[
                "obs",
                "time_step",
            ],
            output_names=[
                "actions",
                "joint_pos",
                "joint_vel",
                "body_pos_w",
                "body_quat_w",
                "body_lin_vel_w",
                "body_ang_vel_w",
            ],
            dynamic_axes={},
        )

        print(
            "[INFO]: Exported ONNX policy to: "
            f"{onnx_path}"
        )


# ============================================================================
# Metadata helpers
# ============================================================================


def list_to_csv_str(
    arr,
    *,
    decimals: int = 3,
    delimiter: str = ",",
) -> str:
    """Convert a flat Python list to CSV-style metadata string."""

    fmt = f"{{:.{decimals}f}}"

    return delimiter.join(
        (
            fmt.format(x)
            if isinstance(
                x,
                (int, float),
            )
            else str(x)
        )
        for x in arr
    )


def _to_cpu_tensor(
    value,
) -> torch.Tensor:
    """
    Convert Isaac Lab / PyTorch tensor-like data to a CPU torch.Tensor.

    Supports:
    - torch.Tensor
    - newer Isaac Lab ProxyArray objects exposing `.torch`
    - generic tensor-like values
    """

    if isinstance(
        value,
        torch.Tensor,
    ):
        return (
            value
            .detach()
            .cpu()
        )

    # Newer Isaac Lab / PhysX ProxyArray compatibility.
    if hasattr(
        value,
        "torch",
    ):
        value = value.torch

        if isinstance(
            value,
            torch.Tensor,
        ):
            return (
                value
                .detach()
                .cpu()
            )

    return (
        torch.as_tensor(
            value
        )
        .detach()
        .cpu()
    )


def _first_env_to_list(
    value,
) -> list:
    """
    Convert articulation data into a flat list.

    Isaac Lab articulation values such as default_joint_pos normally have
    shape:

        [num_envs, num_joints]

    ONNX metadata needs one flat joint vector, so environment 0 is used.
    """

    tensor = _to_cpu_tensor(
        value
    )

    if tensor.ndim >= 2:
        tensor = tensor[0]

    return (
        tensor
        .reshape(-1)
        .tolist()
    )


def _get_default_joint_pos(
    robot_data,
) -> list:
    """
    Obtain nominal/default joint pose across Isaac Lab versions.

    Some custom/older WBT branches used:
        default_joint_pos_nominal

    Standard Isaac Lab uses:
        default_joint_pos
    """

    # ------------------------------------------------------------------------
    # Compatibility with custom WBT / older patched branch.
    # ------------------------------------------------------------------------

    if hasattr(
        robot_data,
        "default_joint_pos_nominal",
    ):
        value = (
            robot_data
            .default_joint_pos_nominal
        )

        print(
            "[INFO]: ONNX metadata default_joint_pos source: "
            "default_joint_pos_nominal"
        )

        return _first_env_to_list(
            value
        )

    # ------------------------------------------------------------------------
    # Standard Isaac Lab API.
    # ------------------------------------------------------------------------

    if hasattr(
        robot_data,
        "default_joint_pos",
    ):
        value = (
            robot_data
            .default_joint_pos
        )

        print(
            "[INFO]: ONNX metadata default_joint_pos source: "
            "default_joint_pos"
        )

        return _first_env_to_list(
            value
        )

    raise AttributeError(
        "Robot ArticulationData has neither "
        "'default_joint_pos_nominal' nor "
        "'default_joint_pos'."
    )


# ============================================================================
# Attach ONNX metadata
# ============================================================================


def attach_onnx_metadata(
    env: ManagerBasedRLEnv,
    run_path: str,
    path: str,
    filename: str = "policy.onnx",
) -> None:
    """Attach deployment metadata to exported ONNX policy."""

    onnx_path = os.path.join(
        path,
        filename,
    )

    if not os.path.isfile(
        onnx_path
    ):
        raise FileNotFoundError(
            "ONNX policy does not exist: "
            f"{onnx_path}"
        )

    # ------------------------------------------------------------------------
    # Policy observation metadata
    # ------------------------------------------------------------------------

    observation_names = (
        env.observation_manager
        .active_terms["policy"]
    )

    observation_history_lengths: list[int] = []

    policy_cfg = (
        env.observation_manager
        .cfg
        .policy
    )

    if (
        policy_cfg.history_length
        is not None
    ):
        observation_history_lengths = (
            [
                policy_cfg.history_length
            ]
            * len(
                observation_names
            )
        )

    else:

        policy_cfg_dict = (
            policy_cfg.to_dict()
        )

        for name in observation_names:

            term_cfg = (
                policy_cfg_dict[
                    name
                ]
            )

            history_length = (
                term_cfg[
                    "history_length"
                ]
            )

            observation_history_lengths.append(
                1
                if history_length == 0
                else history_length
            )

    # ------------------------------------------------------------------------
    # Robot data
    # ------------------------------------------------------------------------

    robot = (
        env.scene[
            "robot"
        ]
    )

    robot_data = (
        robot.data
    )

    # ------------------------------------------------------------------------
    # Default / nominal joint pose
    # ------------------------------------------------------------------------

    default_joint_pos = (
        _get_default_joint_pos(
            robot_data
        )
    )

    # ------------------------------------------------------------------------
    # Joint stiffness / damping
    # ------------------------------------------------------------------------

    joint_stiffness = (
        _first_env_to_list(
            robot_data
            .joint_stiffness
        )
    )

    joint_damping = (
        _first_env_to_list(
            robot_data
            .joint_damping
        )
    )

    # ------------------------------------------------------------------------
    # Action scale
    # ------------------------------------------------------------------------

    joint_pos_action = (
        env.action_manager
        .get_term(
            "joint_pos"
        )
    )

    action_scale = (
        _first_env_to_list(
            joint_pos_action
            ._scale
        )
    )

    # ------------------------------------------------------------------------
    # Motion command
    # ------------------------------------------------------------------------

    motion_command = (
        env.command_manager
        .get_term(
            "motion"
        )
    )

    # ------------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------------

    metadata = {
        "run_path":
            run_path,

        "joint_names":
            robot_data.joint_names,

        "joint_stiffness":
            joint_stiffness,

        "joint_damping":
            joint_damping,

        "default_joint_pos":
            default_joint_pos,

        "command_names":
            env.command_manager.active_terms,

        "observation_names":
            observation_names,

        "observation_history_lengths":
            observation_history_lengths,

        "action_scale":
            action_scale,

        "anchor_body_name":
            motion_command
            .cfg
            .anchor_body_name,

        "body_names":
            motion_command
            .cfg
            .body_names,
    }

    # ------------------------------------------------------------------------
    # Load ONNX
    # ------------------------------------------------------------------------

    model = onnx.load(
        onnx_path
    )

    # ------------------------------------------------------------------------
    # Avoid duplicate metadata entries if export is run repeatedly.
    # ------------------------------------------------------------------------

    existing_keys = {
        entry.key
        for entry
        in model.metadata_props
    }

    for k, v in metadata.items():

        if isinstance(
            v,
            list,
        ):
            value_str = (
                list_to_csv_str(
                    v
                )
            )

        else:
            value_str = str(
                v
            )

        # --------------------------------------------------------------
        # Update existing property.
        # --------------------------------------------------------------

        if k in existing_keys:

            for entry in (
                model.metadata_props
            ):

                if (
                    entry.key
                    ==
                    k
                ):
                    entry.value = (
                        value_str
                    )

                    break

        # --------------------------------------------------------------
        # Add new property.
        # --------------------------------------------------------------

        else:

            entry = (
                onnx.StringStringEntryProto()
            )

            entry.key = k

            entry.value = (
                value_str
            )

            model.metadata_props.append(
                entry
            )

    # ------------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------------

    onnx.save(
        model,
        onnx_path,
    )

    print(
        "[INFO]: Attached ONNX metadata to: "
        f"{onnx_path}"
    )

    print(
        "[INFO]: Metadata joint count = "
        f"{len(default_joint_pos)}"
    )

    print(
        "[INFO]: Metadata default_joint_pos = "
        f"{default_joint_pos}"
    )
