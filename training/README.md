# Training Projects

`training/` 用于存放各项自由搏击策略的训练源码。每个策略都是独立、可安装的训练项目，并在自己的 README 中维护完整使用方法。

## Projects

| Directory | Gym Task | Deployment Policy | Documentation |
|---|---|---|---|
| [`boxing/`](boxing/) | `Unitree-G1-29dof-Boxing` | `Boxing` | [README](boxing/README.md) |
| [`punch/`](punch/) | `Unitree-G1-29dof-Punch` | `Punch` | [README](punch/README.md) |
| [`rightkick/`](rightkick/) | `Unitree-G1-29dof-Rightkick` | `Rightkick` | [README](rightkick/README.md) |
| [`spinkick/`](spinkick/) | `Unitree-G1-29dof-Spinkick` | `Spinkick` | [README](spinkick/README.md) |

## Directory Convention

后续训练项目按以下结构添加：

```text
training/<policy>/
├── README.md                 # 依赖、安装、训练、回放和导出说明
├── checkpoints/             # 需要随仓库管理的基线 checkpoint
├── scripts/                 # 训练、回放和导出入口
└── source/<package>/         # 可编辑安装的 Python package
    ├── pyproject.toml
    └── <package>/
```

命名约定：

- 目录和 Python package 使用小写名称，例如 `boxing`、`punch`、`leftkick`。
- Gym task 使用 `Unitree-G1-29dof-<Policy>` 格式，例如 `Unitree-G1-29dof-Boxing`。
- 部署状态和策略目录使用与 `config.yaml` 一致的名称，例如 `Boxing`。
- 训练日志、视频、缓存和临时构建结果不提交；有复现实验价值的基线 checkpoint 可放入项目的 `checkpoints/`。
- 新增项目后，同时更新本页项目表和仓库根 README 的训练索引。
