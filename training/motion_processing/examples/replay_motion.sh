#!/bin/bash
# 在 Isaac Sim 中回放动作进行可视化验证
# 用法: bash replay_motion.sh <motion_file.npz>

if [ $# -eq 0 ]; then
    echo "用法: bash replay_motion.sh <motion_file.npz>"
    exit 1
fi

MOTION_FILE=$1

if [ ! -f "$MOTION_FILE" ]; then
    echo "错误: 文件不存在 $MOTION_FILE"
    exit 1
fi

echo "=================================="
echo "回放动作: $(basename $MOTION_FILE)"
echo "=================================="

python replay_npz_local.py \
    --motion_file $MOTION_FILE \
    --fps 50

echo ""
echo "回放完成"
