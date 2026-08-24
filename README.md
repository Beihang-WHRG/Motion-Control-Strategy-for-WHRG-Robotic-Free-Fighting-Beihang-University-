# Unitree G1 Boxing Deployment

宇树 G1 29DOF 搏击策略部署框架，包含速度控制、序列动作、倒地检测、自动恢复以及键盘和手柄状态切换。

## Included States

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

移动指令使用 `W/S/A/D/Q/E`，`Z` 清零。速度范围和加速度限制分别读取当前策略 `deploy.yaml` 中的 `ranges` 与 `max_acceleration`。

## Build

依赖 Unitree SDK2、Cyclone DDS C++、Eigen3、Boost program_options、yaml-cpp 和 Zlib。ONNX Runtime 的 x86_64 与 aarch64 运行库已放在 `deploy/thirdparty`。

```bash
cd deploy/robots/g1
cmake -S . -B build
cmake --build build -j4
```

## Run

仿真：

```bash
./build/g1_ctrl -n lo -c config.yaml
```

真机：

```bash
./build/g1_ctrl -n <network-interface> -c config.yaml
```

唯一保留的状态机配置是 `deploy/robots/g1/config/config.yaml`。其中包含完整状态转换、动作结束回到 Boxing、倒地进入 Recovery 和恢复完成回到 Boxing 的配置。

## Policies

- `Boxing/v0`: 最新搏击 locomotion 策略
- `velocity/v0`: 通用 locomotion 策略
- `Recovery/v0`: 倒地恢复策略
- `Punch`, `Leftkick`, `Rightkick`, `spinkick`: motion 序列动作策略

策略目录中的 `joint_ids_map` 表示策略模型顺序到 Unitree SDK 硬件顺序的映射。`stiffness`、`damping`、默认关节位置和动作均按策略模型顺序提供。
