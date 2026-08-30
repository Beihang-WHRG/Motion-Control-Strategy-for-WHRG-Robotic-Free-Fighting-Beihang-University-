# SpinKick Training

回旋踢动作的强化学习训练项目。

## Overview

本项目使用 Whole-Body Tracking 技术训练人形机器人执行回旋踢（飞踢）动作。通过强化学习，机器人能够在保持平衡的同时完成高难度的回旋踢搏击动作。

## Project Structure

```
spinkick/
├── README.md                    # 本文件
├── checkpoints/                 # 训练好的模型检查点和部署文件
│   ├── checkpoints/             # PyTorch 模型文件
│   ├── deploy/                  # 部署用的 CSV 文件
│   ├── onnx/                    # ONNX 格式模型
│   ├── motion.npz               # 动作序列数据
│   ├── policy.onnx              # 策略网络 ONNX 模型
│   └── SOURCE.txt               # 源文件信息
├── scripts/                     # 训练、回放和导出脚本
└── source/spinkick_tracking/    # Python 训练包源码
```

## Features

- 基于 Isaac Lab 的强化学习训练环境
- Whole-Body Tracking 全身运动控制
- 支持 ONNX 模型导出用于实际部署
- 包含抗扰和平衡恢复策略
- 针对高动态回旋动作优化的控制策略

## Dependencies

- Isaac Lab (强化学习训练)
- PyTorch
- ONNX Runtime (部署)
- NumPy

## Training

训练脚本位于 `scripts/rsl_rl/` 目录：

```bash
python scripts/rsl_rl/train.py
```

## Deployment

部署文件位于 `checkpoints/deploy/` 目录，包含 50Hz 的关节轨迹数据。

ONNX 模型位于 `checkpoints/onnx/` 和根目录的 `policy.onnx`，可用于实际机器人部署。

## Motion Data

`motion.npz` 包含参考动作序列，用于模仿学习和轨迹跟踪。

## Notes

本项目是北航人形机器人搏击项目的一部分，展示了纯自研运动控制技术在高动态搏击场景下的应用。回旋踢是搏击动作中难度较高的动作之一，要求机器人具备优秀的全身协调和平衡控制能力。
