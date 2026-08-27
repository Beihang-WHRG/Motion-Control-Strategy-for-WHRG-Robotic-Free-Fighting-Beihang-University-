# Unitree G1 Free-Fighting Policies

宇树 G1 29DOF 自由搏击策略仓库，统一管理策略训练源码、模型参数和部署状态机。

## Repository Layout

```text
.
├── training/                  # 各策略的独立训练项目
│   ├── README.md              # 训练项目索引和目录规范
│   └── boxing/                # Boxing locomotion 训练源码
│       └── README.md          # Boxing 安装、训练和回放说明
└── deploy/                    # G1 推理与状态机部署
    └── robots/g1/
        ├── config/config.yaml
        └── config/policy/
```

训练和部署按策略名称对应：训练项目使用适合 Python 的小写目录名，例如 `training/boxing`；部署策略使用状态机名称，例如 `deploy/robots/g1/config/policy/Boxing`。

## Training

当前训练项目：

| Policy | Task | Source | Guide |
|---|---|---|---|
| Boxing | `Unitree-G1-29dof-Boxing` | [`training/boxing`](training/boxing/) | [Boxing training guide](training/boxing/README.md) |

训练项目的依赖、安装命令、训练阶段、checkpoint 和回放方法由各自目录内的 README 维护。新增策略时，请同时更新 [training/README.md](training/README.md) 中的项目索引。

## Deployment

部署框架包含速度控制、序列动作、倒地检测、自动恢复以及键盘和手柄状态切换。

| ID | State | Purpose | Gamepad | Keyboard |
|---:|---|---|---|---|
| 1 | Passive | 阻尼模式 | `LT+B` | `0` |
| 2 | BoxingFixStand | 搏击站立位姿 | `LT+Up` | `2` |
| 3 | Velocity | 通用 locomotion | `RT+A` | `3` |
| 4 | DefaultFixStand | 官方默认站立位姿 | `LT+Right` | `4` |
| 5 | Boxing | 搏击 locomotion | `RB+A` | `5` |
| 6 | Punch | 拳击序列动作 | `RB+Up` | `6` |
| 7 | Leftkick | 左侧序列动作 | `RB+Left` | `7` |
| 8 | Recovery | 倒地恢复 | 自动或 `LT+Down` | `8` |
| 9 | Rightkick | 右侧序列动作 | `RB+Right` | `9` |
| 10 | SpinKick | 转身踢序列动作 | `RB+Down` | `K` |

移动指令使用 `W/S/A/D/Q/E`，`Z` 清零。速度范围和加速度限制读取当前策略 `deploy.yaml` 中的 `ranges` 与 `max_acceleration`。

### Build

依赖 Unitree SDK2、Cyclone DDS C++、Eigen3、Boost program_options、yaml-cpp 和 Zlib。仓库中包含 x86_64 与 aarch64 的 ONNX Runtime 运行库。

```bash
cd deploy/robots/g1
cmake -S . -B build
cmake --build build -j4
```

### Run

```bash
# Simulation
./build/g1_ctrl -n lo -c config.yaml

# Robot
./build/g1_ctrl -n <network-interface> -c config.yaml
```

状态机配置位于 [`deploy/robots/g1/config/config.yaml`](deploy/robots/g1/config/config.yaml)，包含动作结束返回 Boxing、倒地进入 Recovery 和恢复完成返回 Boxing 的完整流程。

当前部署策略包括 `Boxing`、`velocity`、`Recovery`、`Punch`、`Leftkick`、`Rightkick` 和 `spinkick`。策略目录中的 `joint_ids_map` 表示策略模型顺序到 Unitree SDK 硬件顺序的映射。
