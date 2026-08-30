#!/bin/bash
# 验证处理后的动作数据
# 用法: bash validate_motions.sh

set -e

echo "=================================="
echo "验证处理后的动作数据"
echo "=================================="

MOTION_DIR="./processed_motions"

if [ ! -d "$MOTION_DIR" ]; then
    echo "错误: 未找到动作目录 $MOTION_DIR"
    exit 1
fi

# 查找所有 NPZ 文件
NPZ_FILES=$(find $MOTION_DIR -name "*.npz" -type f)

if [ -z "$NPZ_FILES" ]; then
    echo "错误: 未找到任何 NPZ 文件"
    exit 1
fi

echo "找到以下动作文件："
echo "$NPZ_FILES"
echo ""

# 验证每个文件
for npz_file in $NPZ_FILES; do
    echo "验证: $(basename $npz_file)"
    python validate_motion_npz.py --input_file $npz_file
    echo ""
done

echo "=================================="
echo "所有动作验证完成！"
echo "=================================="
