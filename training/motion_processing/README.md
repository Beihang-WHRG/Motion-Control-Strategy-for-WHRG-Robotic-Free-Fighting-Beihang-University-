# Motion Data Processing

动作数据处理工具集，用于将原始动作数据（CSV 格式）转换为训练和部署所需的格式（NPZ 格式）。

## 概述

本工具集实现了完整的动作数据处理流程，包括：
- **动作裁剪**：从原始动作序列中提取特定帧范围
- **帧率插值**：将动作数据从输入帧率转换到目标帧率
- **数据验证**：在 Isaac Sim 中回放并验证处理后的动作
- **格式转换**：将处理后的数据保存为 NPZ 格式供训练使用

## 核心功能

### 1. 动作裁剪（Frame Range Cropping）

通过 `--frame_range` 参数指定需要提取的帧范围，可以从完整动作序列中裁剪出关键片段。

**用途：**
- 去除动作开始和结束时的无效帧
- 提取动作的核心执行阶段
- 移除过渡和准备阶段

**示例：**
```bash
# 从第 122 帧到第 722 帧（包含两端）
--frame_range 122 722
```

### 2. 帧率插值（Frame Interpolation）

使用线性插值（LERP）和球面线性插值（SLERP）技术，将动作数据从输入帧率转换到目标帧率。

**插值方法：**
- **位置数据**：线性插值（LERP）
- **旋转数据**：球面线性插值（SLERP）- 保证旋转的平滑性
- **关节角度**：线性插值（LERP）

**用途：**
- 匹配机器人控制频率（通常 50Hz）
- 平滑动作轨迹
- 生成更细腻的中间帧

**算法实现：**
```python
# 时间插值
times = torch.arange(0, duration, output_dt)

# 计算插值权重
phase = times / duration
index_0 = floor(phase * (input_frames - 1))
index_1 = min(index_0 + 1, input_frames - 1)
blend = phase * (input_frames - 1) - index_0

# 位置插值（LERP）
pos_interpolated = pos[index_0] * (1 - blend) + pos[index_1] * blend

# 旋转插值（SLERP）
quat_interpolated = slerp(quat[index_0], quat[index_1], blend)
```

### 3. 速度计算

基于插值后的位置和姿态数据，自动计算线性速度和角速度：

- **线性速度**：位置对时间的梯度
- **角速度**：使用 SO(3) 导数计算旋转速度
- **关节速度**：关节角度对时间的梯度

## 工具脚本

### csv_to_npz.py

标准的 CSV 到 NPZ 转换工具，支持完整的裁剪和插值功能。

**参数：**
- `--input_file`：输入的 CSV 文件路径
- `--input_fps`：输入动作的帧率（默认 30）
- `--frame_range`：帧范围 [起始帧, 结束帧]（可选）
- `--output_name`：输出的 NPZ 文件名称
- `--output_fps`：输出动作的帧率（默认 50）

### csv_to_npz_local.py

本地版本的转换工具，不依赖 wandb 上传。

### csv_to_npz_g9_exactfps.py

针对 G9 机器人优化的精确帧率版本。

### replay_npz.py / replay_npz_local.py

在 Isaac Sim 中回放 NPZ 文件，用于验证动作数据的正确性。

### validate_motion_npz.py

验证 NPZ 文件的数据完整性和格式正确性。

## 使用示例

### 示例 1：基础转换（无裁剪）

将 30fps 的动作转换为 50fps，不裁剪：

```bash
python csv_to_npz.py \
    --input_file ./raw_data/punch_motion.csv \
    --input_fps 30 \
    --output_name punch_motion \
    --output_fps 50
```

### 示例 2：裁剪并插值

从 30fps 动作中提取第 100-500 帧，转换为 50fps：

```bash
python csv_to_npz.py \
    --input_file ./raw_data/rightkick_motion.csv \
    --input_fps 30 \
    --frame_range 100 500 \
    --output_name rightkick_motion \
    --output_fps 50
```

**处理结果：**
- 输入：401 帧 @ 30fps（约 13.37 秒）
- 输出：668 帧 @ 50fps（约 13.36 秒）

### 示例 3：批量处理多个动作

```bash
#!/bin/bash

# 打拳动作 - 提取核心出拳阶段
python csv_to_npz.py \
    --input_file ./raw_data/punch.csv \
    --input_fps 30 \
    --frame_range 122 722 \
    --output_name punch_core \
    --output_fps 50

# 右踢动作 - 提取踢腿阶段
python csv_to_npz.py \
    --input_file ./raw_data/rightkick.csv \
    --input_fps 30 \
    --frame_range 80 450 \
    --output_name rightkick_core \
    --output_fps 50

# 回旋踢 - 完整动作序列
python csv_to_npz.py \
    --input_file ./raw_data/spinkick.csv \
    --input_fps 30 \
    --output_name spinkick_full \
    --output_fps 50
```

### 示例 4：验证处理结果

```bash
# 回放动作验证
python replay_npz_local.py \
    --motion_file ./output/punch_core.npz \
    --fps 50

# 数据完整性验证
python validate_motion_npz.py \
    --input_file ./output/punch_core.npz
```

## 数据格式

### 输入格式（CSV）

CSV 文件每行代表一帧，列格式如下：

```
px, py, pz, qx, qy, qz, qw, j1, j2, ..., j29
```

- `px, py, pz`：基座位置（3列）
- `qx, qy, qz, qw`：基座旋转四元数（4列）
- `j1-j29`：29个关节角度（29列）

**注意**：输入的四元数格式为 `(x, y, z, w)`，工具会自动转换为 Isaac Sim 的 `(w, x, y, z)` 格式。

### 输出格式（NPZ）

NPZ 文件包含以下数据数组：

```python
{
    'fps': [50],                    # 帧率
    'joint_pos': (N, 29),           # 关节位置
    'joint_vel': (N, 29),           # 关节速度
    'body_pos_w': (N, num_bodies, 3),    # 所有刚体位置
    'body_quat_w': (N, num_bodies, 4),   # 所有刚体旋转
    'body_lin_vel_w': (N, num_bodies, 3), # 所有刚体线速度
    'body_ang_vel_w': (N, num_bodies, 3)  # 所有刚体角速度
}
```

## 最佳实践

### 1. 确定裁剪范围

使用可视化工具查看原始 CSV 数据，确定动作的关键阶段：

```python
import numpy as np
import matplotlib.pyplot as plt

# 加载并可视化关节轨迹
data = np.loadtxt('motion.csv', delimiter=',')
plt.plot(data[:, 7:])  # 绘制所有关节角度
plt.xlabel('Frame')
plt.ylabel('Joint Angle (rad)')
plt.show()
```

找出动作开始、执行、结束的关键帧。

### 2. 选择合适的帧率

- **训练用途**：50Hz（与仿真和部署一致）
- **可视化展示**：30Hz 或 60Hz
- **快速原型**：25Hz

### 3. 验证处理结果

每次处理后都应该：
1. 检查输出日志中的帧数和时长
2. 使用 `replay_npz_local.py` 在仿真中回放
3. 验证动作的连续性和平滑度

### 4. 数据质量检查

处理前检查原始数据：
- 是否有缺失帧
- 关节角度是否在合理范围内
- 基座位置是否异常

## 工作流程

```
原始动作捕捉/仿真数据 (CSV)
    ↓
1. 可视化分析，确定裁剪范围
    ↓
2. 使用 csv_to_npz.py 处理
   - 裁剪帧范围
   - 帧率插值
   - 计算速度
    ↓
3. 回放验证 (replay_npz_local.py)
    ↓
4. 用于训练或部署
```

## 技术细节

### SLERP 实现

球面线性插值用于四元数旋转，保证旋转的最短路径和恒定角速度：

```python
def quat_slerp(q0, q1, t):
    """
    q0, q1: 起始和结束四元数 (w, x, y, z)
    t: 插值参数 [0, 1]
    """
    dot = torch.sum(q0 * q1)
    
    # 确保最短路径
    if dot < 0:
        q1 = -q1
        dot = -dot
    
    # 球面插值
    theta = torch.acos(torch.clamp(dot, -1, 1))
    sin_theta = torch.sin(theta)
    
    if sin_theta < 1e-6:
        # 线性插值（角度很小时）
        return q0 * (1 - t) + q1 * t
    
    w0 = torch.sin((1 - t) * theta) / sin_theta
    w1 = torch.sin(t * theta) / sin_theta
    
    return w0 * q0 + w1 * q1
```

### SO(3) 角速度计算

从四元数序列计算角速度：

```python
def compute_angular_velocity(quats, dt):
    """
    quats: (N, 4) 四元数序列
    dt: 时间步长
    返回: (N, 3) 角速度
    """
    q_prev, q_next = quats[:-2], quats[2:]
    q_rel = quat_mul(q_next, quat_conjugate(q_prev))
    omega = axis_angle_from_quat(q_rel) / (2.0 * dt)
    
    # 边界处理
    omega = torch.cat([omega[:1], omega, omega[-1:]], dim=0)
    return omega
```

## 依赖项

- Isaac Lab
- PyTorch
- NumPy
- Weights & Biases (wandb) - 可选，用于数据管理

## 故障排除

### 问题：插值后动作不平滑

**解决方案：**
- 检查输入数据是否有突变
- 增加输出帧率
- 检查裁剪范围是否合适

### 问题：速度计算异常

**解决方案：**
- 确保帧率设置正确
- 检查时间步长计算
- 验证插值结果

### 问题：四元数不连续

**解决方案：**
- 使用 SLERP 而非 LERP
- 检查输入四元数是否归一化
- 确保四元数符号一致性

## 参考资料

- [Isaac Lab Documentation](https://isaac-sim.github.io/IsaacLab/)
- [Quaternion SLERP](https://en.wikipedia.org/wiki/Slerp)
- [Motion Retargeting for Humanoid Robots](https://arxiv.org/abs/2008.11738)

## 贡献者

北航人形机器人团队 - 运动控制组
