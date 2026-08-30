#!/bin/bash
# 批量处理搏击动作数据
# 用法: bash process_all_motions.sh

set -e

echo "=================================="
echo "批量处理搏击动作数据"
echo "=================================="

# 输入和输出目录
INPUT_DIR="./raw_data"
OUTPUT_DIR="./processed_motions"

# 创建输出目录
mkdir -p $OUTPUT_DIR

# 打拳动作处理
echo ""
echo "[1/3] 处理打拳动作..."
python csv_to_npz.py \
    --input_file ${INPUT_DIR}/punch.csv \
    --input_fps 30 \
    --frame_range 122 722 \
    --output_name punch_motion \
    --output_fps 50 \
    --headless

echo "✓ 打拳动作处理完成"

# 右踢动作处理
echo ""
echo "[2/3] 处理右踢动作..."
python csv_to_npz.py \
    --input_file ${INPUT_DIR}/rightkick.csv \
    --input_fps 30 \
    --frame_range 80 450 \
    --output_name rightkick_motion \
    --output_fps 50 \
    --headless

echo "✓ 右踢动作处理完成"

# 回旋踢动作处理
echo ""
echo "[3/3] 处理回旋踢动作..."
python csv_to_npz.py \
    --input_file ${INPUT_DIR}/spinkick.csv \
    --input_fps 30 \
    --frame_range 50 600 \
    --output_name spinkick_motion \
    --output_fps 50 \
    --headless

echo "✓ 回旋踢动作处理完成"

echo ""
echo "=================================="
echo "所有动作处理完成！"
echo "输出目录: $OUTPUT_DIR"
echo "=================================="

# 列出生成的文件
echo ""
echo "生成的文件："
ls -lh ${OUTPUT_DIR}/*.npz 2>/dev/null || echo "未找到 NPZ 文件"
