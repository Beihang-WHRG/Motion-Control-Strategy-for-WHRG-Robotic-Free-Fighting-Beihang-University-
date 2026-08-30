"""
可视化动作数据的关节轨迹
用于确定合适的裁剪范围
"""

import numpy as np
import matplotlib.pyplot as plt
import argparse

def visualize_motion(csv_file, joint_names=None):
    """
    可视化 CSV 文件中的关节轨迹

    Args:
        csv_file: CSV 文件路径
        joint_names: 关节名称列表（可选）
    """
    # 加载数据
    data = np.loadtxt(csv_file, delimiter=',')

    print(f"数据形状: {data.shape}")
    print(f"总帧数: {data.shape[0]}")
    print(f"总列数: {data.shape[1]} (3 位置 + 4 四元数 + {data.shape[1]-7} 关节)")

    # 提取关节角度 (跳过前7列：3位置 + 4四元数)
    joint_data = data[:, 7:]
    num_joints = joint_data.shape[1]

    # 创建图表
    fig, axes = plt.subplots(5, 6, figsize=(20, 15))
    axes = axes.flatten()

    # 绘制每个关节的轨迹
    for i in range(min(num_joints, 30)):
        ax = axes[i]
        ax.plot(joint_data[:, i])

        if joint_names and i < len(joint_names):
            title = joint_names[i]
        else:
            title = f"Joint {i+1}"

        ax.set_title(title, fontsize=8)
        ax.set_xlabel('Frame')
        ax.set_ylabel('Angle (rad)')
        ax.grid(True, alpha=0.3)

    # 隐藏多余的子图
    for i in range(num_joints, len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    plt.suptitle(f'Motion Joint Trajectories: {csv_file}', y=1.001, fontsize=14)

    # 显示并保存
    output_file = csv_file.replace('.csv', '_visualization.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n可视化图保存到: {output_file}")
    plt.show()

    # 打印统计信息
    print("\n关节角度统计:")
    print(f"最小值: {joint_data.min():.3f} rad")
    print(f"最大值: {joint_data.max():.3f} rad")
    print(f"均值: {joint_data.mean():.3f} rad")
    print(f"标准差: {joint_data.std():.3f} rad")

    return data

def analyze_motion_phases(csv_file, threshold=0.1):
    """
    分析动作的不同阶段，辅助确定裁剪范围

    Args:
        csv_file: CSV 文件路径
        threshold: 运动阈值（用于检测动作开始和结束）
    """
    data = np.loadtxt(csv_file, delimiter=',')
    joint_data = data[:, 7:]

    # 计算关节速度（相邻帧差分）
    joint_velocity = np.diff(joint_data, axis=0)
    velocity_magnitude = np.linalg.norm(joint_velocity, axis=1)

    # 找到运动显著的帧
    active_frames = np.where(velocity_magnitude > threshold)[0]

    if len(active_frames) > 0:
        motion_start = active_frames[0]
        motion_end = active_frames[-1]

        print(f"\n动作阶段分析:")
        print(f"总帧数: {data.shape[0]}")
        print(f"检测到的动作开始帧: {motion_start}")
        print(f"检测到的动作结束帧: {motion_end}")
        print(f"建议裁剪范围: --frame_range {motion_start} {motion_end}")
    else:
        print("\n未检测到明显的运动阶段，可能需要调整阈值")

    # 绘制速度曲线
    plt.figure(figsize=(12, 4))
    plt.plot(velocity_magnitude)
    plt.axhline(y=threshold, color='r', linestyle='--', label='Threshold')
    if len(active_frames) > 0:
        plt.axvline(x=motion_start, color='g', linestyle='--', label='Motion Start')
        plt.axvline(x=motion_end, color='b', linestyle='--', label='Motion End')
    plt.xlabel('Frame')
    plt.ylabel('Joint Velocity Magnitude')
    plt.title('Motion Activity Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)

    output_file = csv_file.replace('.csv', '_activity.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"活动分析图保存到: {output_file}")
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="可视化动作数据")
    parser.add_argument("--input_file", type=str, required=True, help="输入的 CSV 文件")
    parser.add_argument("--threshold", type=float, default=0.1, help="运动检测阈值")
    parser.add_argument("--analyze", action="store_true", help="分析动作阶段")

    args = parser.parse_args()

    # G1 机器人关节名称
    joint_names = [
        "L_hip_pitch", "L_hip_roll", "L_hip_yaw",
        "L_knee", "L_ankle_pitch", "L_ankle_roll",
        "R_hip_pitch", "R_hip_roll", "R_hip_yaw",
        "R_knee", "R_ankle_pitch", "R_ankle_roll",
        "waist_yaw", "waist_roll", "waist_pitch",
        "L_shoulder_pitch", "L_shoulder_roll", "L_shoulder_yaw",
        "L_elbow", "L_wrist_roll", "L_wrist_pitch", "L_wrist_yaw",
        "R_shoulder_pitch", "R_shoulder_roll", "R_shoulder_yaw",
        "R_elbow", "R_wrist_roll", "R_wrist_pitch", "R_wrist_yaw",
    ]

    # 可视化关节轨迹
    visualize_motion(args.input_file, joint_names)

    # 分析动作阶段
    if args.analyze:
        analyze_motion_phases(args.input_file, args.threshold)
