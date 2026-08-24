#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include "isaaclab/envs/manager_based_rl_env.h"

namespace isaaclab
{
namespace mdp
{

// 机体坐标系下的重力投影：直立时 z = -1，倾角 θ 时 z = -cos(θ)，
// 故机体倾角 = acos(-z)。超过 limit_angle（弧度）判定为姿态异常（摔倒）。
// 数据源为 IMU 四元数（projected_gravity_b），仿真/实机通用。
inline bool bad_orientation(ManagerBasedRLEnv* env, float limit_angle = 1.0)
{
    auto & asset = env->robot;
    auto & data = asset->data.projected_gravity_b;
    return std::fabs(std::acos(-data[2])) > limit_angle;
}

// 比较机器人当前重力投影与参考姿态下的重力投影，只衡量 roll/pitch
// 误差，不受机器人与参考动作之间的全局 yaw 偏差影响。
inline float reference_gravity_error(
    ManagerBasedRLEnv* env,
    const Eigen::Quaternionf& reference_quat_w
)
{
    const auto& data = env->robot->data;
    const float quat_norm = reference_quat_w.norm();
    const float measured_norm = data.projected_gravity_b.norm();
    if (!std::isfinite(quat_norm) || quat_norm < 1e-6f ||
        !std::isfinite(measured_norm) || measured_norm < 1e-6f)
    {
        return std::numeric_limits<float>::infinity();
    }

    const Eigen::Quaternionf normalized_reference(
        reference_quat_w.coeffs() / quat_norm
    );
    const Eigen::Vector3f reference_gravity_b =
        normalized_reference.conjugate() * data.GRAVITY_VEC_W;
    const float reference_norm = reference_gravity_b.norm();
    if (!std::isfinite(reference_norm) || reference_norm < 1e-6f)
    {
        return std::numeric_limits<float>::infinity();
    }

    const float cosine = std::clamp(
        data.projected_gravity_b.dot(reference_gravity_b) /
            (measured_norm * reference_norm),
        -1.0f,
        1.0f
    );
    return std::acos(cosine);
}

inline bool bad_reference_gravity(
    ManagerBasedRLEnv* env,
    const Eigen::Quaternionf& reference_quat_w,
    float limit_angle
)
{
    return reference_gravity_error(env, reference_quat_w) > limit_angle;
}

} 
} 
