# 动作处理配置文件
# 定义各个动作的处理参数

# 打拳动作
PUNCH_INPUT="./raw_data/punch.csv"
PUNCH_INPUT_FPS=30
PUNCH_FRAME_START=122
PUNCH_FRAME_END=722
PUNCH_OUTPUT_FPS=50
PUNCH_OUTPUT_NAME="punch_motion"

# 右踢动作
RIGHTKICK_INPUT="./raw_data/rightkick.csv"
RIGHTKICK_INPUT_FPS=30
RIGHTKICK_FRAME_START=80
RIGHTKICK_FRAME_END=450
RIGHTKICK_OUTPUT_FPS=50
RIGHTKICK_OUTPUT_NAME="rightkick_motion"

# 回旋踢动作
SPINKICK_INPUT="./raw_data/spinkick.csv"
SPINKICK_INPUT_FPS=30
SPINKICK_FRAME_START=50
SPINKICK_FRAME_END=600
SPINKICK_OUTPUT_FPS=50
SPINKICK_OUTPUT_NAME="spinkick_motion"

# 通用设置
OUTPUT_DIR="./processed_motions"
RAW_DATA_DIR="./raw_data"

# 说明：
# - FRAME_START 和 FRAME_END 是基于 1 的索引（第一帧是 1）
# - 输出帧率建议设置为 50Hz，与机器人控制频率一致
# - 可以根据实际动作数据调整裁剪范围
