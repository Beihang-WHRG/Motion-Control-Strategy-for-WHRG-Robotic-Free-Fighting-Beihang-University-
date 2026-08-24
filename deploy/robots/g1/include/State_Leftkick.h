#pragma once

#include <atomic>
#include <chrono>
#include <cmath>
#include <mutex>
#include <optional>
#include "unitree/dds_wrapper/robots/go2/go2.h"
#include "FSM/State_RLBase.h"
#include "State_Mimic.h"  // 复用 State_Mimic::MotionLoader_ (npz 加载/帧推进)
#include <cnpy.h>

/**
 * State_Leftkick: G1 动作跟踪策略状态（Leftkick / Rightkick 共用）
 *
 * 观测结构（与 Punch 同构，使用策略模型关节顺序）:
 *   - 观测 154 维（无历史；喂原始观测）:
 *       [ref_q(29) + ref_dq(29) + anchor_ori_6d(6) + base_gyro(3)
 *        + q-default(29) + dq(29) + last_action(29)]
 *   - 输入 obs[1,154]，新版模型另有 time_step[1,1] motion 帧索引
 *   - 动作: target = default_joint_pos + action_scale * actions（qpos 序）
 *   - 关节顺序: motion.npz/ONNX 模型顺序，经 joint_ids_map 映射到硬件
 *
 * 行为: 进入即从头播放 motion；RB + A（或键盘 r）可随时重新播放；
 *      播完自动切回 end_state（如 Boxing）。
 * 配置（config yaml 中该状态块）:
 *   end_state                      : 播完自动切换的目标状态（如 Boxing）
 *   enable_bad_orientation_check / bad_orientation_limit : 姿态保护
 *   fall_detection                 : 相对当前 motion 帧的重力方向误差或高度超限后切目标
 */
class State_Leftkick : public FSMState
{
public:
    State_Leftkick(int state_mode, std::string state_string);

    void enter();
    void run();
    void exit()
    {
        policy_thread_running = false;
        if (policy_thread.joinable()) {
            policy_thread.join();
        }
    }

    using MotionLoader_ = State_Mimic::MotionLoader_;

private:
    void advance_frame();
    void replay_motion();                     // 重播：帧回零 + 重新对齐 + 清 last_action
    Eigen::Quaternionf robot_torso_quat();    // IMU(pelvis) 朝向 + 腰部关节 -> torso 朝向
    Eigen::Quaternionf motion_torso_quat();   // motion root(pelvis) + 腰部关节 -> torso 朝向
    std::unordered_map<std::string, std::vector<float>> build_obs_map();

    // 摔倒/恢复辅助（与 State_RLBase 一致）
    bool read_base_height(float &height) const;
    bool condition_confirmed(bool condition,
                             std::optional<std::chrono::steady_clock::time_point> &since,
                             int confirm_ms);

    std::unique_ptr<isaaclab::ManagerBasedRLEnv> env;
    std::shared_ptr<MotionLoader_> motion_;

    std::thread policy_thread;
    bool policy_thread_running = false;

    std::atomic<int> frame_{0};   // 当前 motion 帧（策略线程写，FSM 线程读）
    int num_frames_ = 0;

    // 腰部关节在模型 joint_names 中的索引，从 ONNX metadata 解析；
    // 默认值保留 Leftkick 策略的 qpos 序 12/13/14 兼容性。
    int waist_yaw_idx_   = 12;
    int waist_roll_idx_  = 13;
    int waist_pitch_idx_ = 14;

    // 初始偏航对齐（世界系 -> 机器人初始朝向系），消除机器人与 motion 初始朝向差
    Eigen::Matrix3f init_rot_ = Eigen::Matrix3f::Identity();

    // 重播信号（RB + A 同时按下）边沿检测
    bool last_restart_key_ = false;
    bool has_played_ = false;   // 已触发过播放（用于播完自动回 end_state）

    // 仿真 root 高度数据源（摔倒检测用）；真机为 nullptr
    std::shared_ptr<unitree::robot::go2::subscription::SportModeState> sport_mode_state;
    std::optional<std::chrono::steady_clock::time_point> fall_condition_since_;
};


REGISTER_FSM(State_Leftkick)
