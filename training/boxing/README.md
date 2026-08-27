# G1 Boxing Training

这是 G1 29DOF `Boxing` locomotion 策略的独立 Isaac Lab 训练项目，与部署状态 `Boxing` 对应。基础任务训练速度跟踪和搏击站姿下的移动能力，第二阶段可在同一策略上进行固定 Push 微调。

## Task IDs

- 基础训练：`Unitree-G1-29dof-Boxing`
- 固定 Push 微调：`Unitree-G1-29dof-Boxing-Push`

Push 任务只额外启用固定 interval push，不包含 push curriculum。建议先完成基础训练，再进行抗扰微调。

## Dependencies

- Isaac Sim 5.1.0
- Isaac Lab 2.3.0
- RSL-RL
- 已安装的 `unitree_rl_lab`
- `unitree_rl_lab.assets.robots.unitree.UNITREE_MODEL_DIR` 已指向 G1 USD 模型目录

本项目复用 `unitree_rl_lab` 的 G1 模型和执行器参数。Boxing 初始 root pose 与 29 个关节默认位置定义在 `source/boxing/boxing/assets/robot.py`。

## Layout

```text
training/boxing/
├── checkpoints/
│   └── model_25000.pt
├── scripts/rsl_rl/
│   ├── cli_args.py
│   ├── play.py
│   └── train.py
└── source/boxing/
    ├── pyproject.toml
    └── boxing/
        ├── assets/robot.py
        └── tasks/boxing/
            ├── agents/rsl_rl_ppo_cfg.py
            ├── mdp/
            │   ├── commands.py
            │   ├── curriculums.py
            │   ├── rewards.py
            │   └── terminations.py
            ├── env_cfg.py
            └── push_env_cfg.py
```

## Installation

在已配置 Isaac Lab 和 `unitree_rl_lab` 的 Python 环境中执行：

```bash
cd training/boxing
python -m pip install -e source/boxing
```

安装后，导入 `boxing` 会注册上述两个 Gym task。

## Baseline Checkpoint

`checkpoints/model_25000.pt` 是基础训练的续训起点：

- 文件大小约 9.6 MiB；
- SHA-256：`0639b8617c44356e45e047731cdd7a0ef04c4edc21b066c4416a2dee96384361`；
- 训练入口支持直接传入 checkpoint 路径，不需要复制到 `logs/`。

建议从该 checkpoint 续训。Boxing 默认姿态具有屈膝、身体倾角和左右不对称关节位置，从随机策略开始时容易收敛到只保持站立的局部最优。

## Stage 1: Boxing Locomotion

从基线 checkpoint 继续基础任务：

```bash
python scripts/rsl_rl/train.py \
  --headless \
  --checkpoint checkpoints/model_25000.pt \
  --num_envs 4096 \
  --max_iterations 10000 \
  --run_name locomotion
```

`--max_iterations` 表示本次追加的训练迭代数。判断收敛时应同时检查速度 tracking、平均 episode length 和 play 中的实际步态。

从本项目产生的 checkpoint 继续训练：

```bash
python scripts/rsl_rl/train.py \
  --headless \
  --checkpoint logs/rsl_rl/unitree_g1_29dof_boxing/<run>/model_<iteration>.pt \
  --max_iterations 5000 \
  --run_name locomotion_continue
```

## Stage 2: Push Fine-Tuning

基础步态收敛后，选择 Push task 并加载第一阶段最后一个 checkpoint：

```bash
python scripts/rsl_rl/train.py \
  --headless \
  --task Unitree-G1-29dof-Boxing-Push \
  --checkpoint logs/rsl_rl/unitree_g1_29dof_boxing/<run>/model_<iteration>.pt \
  --experiment_name unitree_g1_29dof_boxing_push \
  --max_iterations 10000 \
  --run_name mild_push
```

Push 参数位于 `source/boxing/boxing/tasks/boxing/push_env_cfg.py`：间隔 `8~12 s`，x 方向 `±0.30 m/s`，y 方向 `±0.25 m/s`，其余方向为 0。确认 tracking 和恢复能力稳定后再手动提高幅度。

## Playback

```bash
python scripts/rsl_rl/play.py \
  --checkpoint checkpoints/model_25000.pt
```

也可以用 `--task Unitree-G1-29dof-Boxing-Push` 回放 Push 环境。训练日志默认写入 `logs/rsl_rl/unitree_g1_29dof_boxing/`。

## Deployment Mapping

部署策略位于 [`deploy/robots/g1/config/policy/Boxing/v0/`](../../deploy/robots/g1/config/policy/Boxing/v0/)。训练产生的新 checkpoint 经过导出和 sim2sim 验证后，再更新该目录中的 `exported/policy.onnx`、`params/agent.yaml`、`params/env.yaml` 和 `params/deploy.yaml`；训练脚本不会自动覆盖部署模型。
