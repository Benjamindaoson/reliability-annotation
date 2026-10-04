"""
OSWorld 轨迹标注工具 - 简化版（中文界面）
直接显示截图，简单选择失败类型

使用方法：
    python -m streamlit run annotation_tool/app_simple.py
"""

import json
import os
from pathlib import Path
from typing import Optional
import streamlit as st

# ============================================================
# 配置
# ============================================================
DATA_DIR = Path("data/external/osworld_verified/claude-4-sonnet-15steps/claude-4-sonnet-20250514-15steps")
ANNOTATION_FILE = Path("data/human_annotations/annotations.jsonl")

# 失败类型定义（简化中文版）
FAILURE_TYPES = {
    "无失败": "整个轨迹没有出现任何实质性的失败",
    "动作错误（SELECTION）": "智能体做了【错误的选择】—— 它本应该做A，但它做了B",
    "执行失败（EXECUTION）": "智能体想做对的事，但【执行出了问题】—— 比如点错了位置",
    "未察觉（RECOGNITION）": "智能体做了错事但【没有注意到】—— 继续往下走好像什么都没发生",
    "恢复失败（RECOVERY）": "智能体【发现出了问题】但尝试的修复方法不对",
}

# 检测证据关键词
DETECTION_KEYWORDS = ["失败", "错误", "不对", "出了问题", "再试", "重试", "let me", "try again", "wrong", "failed", "error"]


# ============================================================
# 数据加载函数
# ============================================================
def find_all_trajectories() -> list[dict]:
    """扫描所有 traj.jsonl 文件"""
    trajectories = []

    if not DATA_DIR.exists():
        return trajectories

    # 遍历任务类型目录（如 libreoffice_writer）
    for task_type_dir in DATA_DIR.iterdir():
        if not task_type_dir.is_dir():
            continue

        # 遍历每个具体轨迹的 UUID 目录
        for traj_dir in task_type_dir.iterdir():
            if not traj_dir.is_dir():
                continue
            traj_file = traj_dir / "traj.jsonl"
            if not traj_file.exists():
                continue

            # 读取轨迹
            steps = []
            with open(traj_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        steps.append(json.loads(line))

            if not steps:
                continue

            trajectories.append({
                "trajectory_id": f"{task_type_dir.name}/{traj_dir.name}",
                "task_id": task_type_dir.name,
                "traj_uuid": traj_dir.name,
                "task_dir": str(traj_dir),
                "steps": steps,
                "final_result": "success" if steps[-1].get("done") and steps[-1].get("reward", 0) > 0 else "failure"
            })

    return trajectories


def load_existing_annotations() -> set[str]:
    """加载已标注的轨迹ID"""
    if not ANNOTATION_FILE.exists():
        return set()

    annotated = set()
    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                ann = json.loads(line)
                annotated.add(ann.get("trajectory_id", ""))
    return annotated


def save_annotation(annotation: dict):
    """保存标注"""
    ANNOTATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ANNOTATION_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(annotation, ensure_ascii=False) + '\n')


def check_if_agent_detected_failure(step: dict) -> tuple[bool, str]:
    """检查智能体是否在推理中提到失败"""
    # 从 action 的 command 字段提取推理
    action = step.get("action", {})
    if isinstance(action, dict):
        command = action.get("command", "")
    else:
        command = str(action)

    command_lower = command.lower()
    for kw in DETECTION_KEYWORDS:
        if kw.lower() in command_lower:
            return True, f"检测到关键词: {kw}"

    return False, ""


# ============================================================
# Streamlit 界面
# ============================================================
st.set_page_config(
    page_title="OSWorld 轨迹标注",
    page_icon="🖥️",
    layout="wide"
)

st.title("🖥️ OSWorld 智能体轨迹标注工具")
st.markdown("**这是一份真实的研究数据，请认真阅读后再标注。**")

# 初始化 session state
if 'trajectories' not in st.session_state:
    st.session_state.trajectories = []
    st.session_state.current_idx = 0
    st.session_state.annotated = set()
    st.session_state.step_idx = 0  # 当前查看的步骤

# 侧边栏
with st.sidebar:
    st.header("📂 数据加载")

    if st.button("🔄 加载轨迹数据", type="primary"):
        with st.spinner("正在加载..."):
            st.session_state.trajectories = find_all_trajectories()
            st.session_state.annotated = load_existing_annotations()
            st.session_state.current_idx = 0
            st.session_state.step_idx = 0
            st.success(f"✅ 加载了 {len(st.session_state.trajectories)} 条轨迹")

    if st.session_state.trajectories:
        # 统计
        total = len(st.session_state.trajectories)
        done = len(st.session_state.annotated)
        remaining = total - done

        st.markdown("---")
        st.markdown(f"**总计：** {total}")
        st.markdown(f"**已标注：** {done}")
        st.markdown(f"**剩余：** {remaining}")

        if remaining > 0:
            st.progress(done / total)

        # 导航
        st.markdown("---")
        st.subheader("🧭 导航")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀ 上一个") and st.session_state.current_idx > 0:
                st.session_state.current_idx -= 1
                st.session_state.step_idx = 0
        with col2:
            if st.button("下一个 ▶"):
                st.session_state.current_idx = min(
                    st.session_state.current_idx + 1,
                    total - 1
                )
                st.session_state.step_idx = 0

        st.number_input(
            "跳到第几条：",
            min_value=1,
            max_value=total,
            value=st.session_state.current_idx + 1,
            key="jump_input"
        )
        if st.button("跳转"):
            st.session_state.current_idx = st.session_state.jump_input - 1
            st.session_state.step_idx = 0
            st.rerun()

        # 失败类型统计
        if st.session_state.annotated:
            st.markdown("---")
            st.subheader("📊 标注统计")
            type_counts = {}
            with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        ann = json.loads(line)
                        ft = ann.get("failure_type", "未知")
                        type_counts[ft] = type_counts.get(ft, 0) + 1
            for ft, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                st.markdown(f"- {ft}: {count}")

# 主内容区
if not st.session_state.trajectories:
    st.info("👈 请先点击左侧的「加载轨迹数据」按钮")
else:
    # 获取未标注的轨迹
    unannotated = [
        (i, t) for i, t in enumerate(st.session_state.trajectories)
        if t["trajectory_id"] not in st.session_state.annotated
    ]

    if not unannotated:
        st.success("🎉 全部轨迹都已标注完成！")
        st.balloons()
    else:
        # 如果当前索引超出了范围，重置
        if st.session_state.current_idx >= len(unannotated):
            st.session_state.current_idx = 0
            st.session_state.step_idx = 0

        # 获取当前轨迹
        actual_idx, traj = unannotated[st.session_state.current_idx]
        traj_id = traj["trajectory_id"]
        task_dir = Path(traj["task_dir"])
        steps = traj["steps"]

        # ========== 任务信息 ==========
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("轨迹编号", f"{st.session_state.current_idx + 1} / {len(unannotated)}")
        with col2:
            st.metric("任务类型", traj["task_id"])
        with col3:
            result = traj["final_result"]
            color = "🟢" if result == "success" else "🔴"
            st.metric("最终结果", f"{color} {result}")

        st.markdown(f"**轨迹ID:** `{traj_id}`")
        st.markdown(f"**总步数:** {len(steps)}")

        # ========== 步骤浏览器 ==========
        st.markdown("---")
        st.subheader(f"📋 轨迹步骤浏览器（当前：第 {st.session_state.step_idx + 1} / {len(steps)} 步）")

        # 步骤导航
        step_col1, step_col2, step_col3, step_col4 = st.columns([1, 1, 1, 4])
        with step_col1:
            if st.button("⏮️ 第一步") and st.session_state.step_idx > 0:
                st.session_state.step_idx = 0
        with step_col2:
            if st.button("◀ 上一张") and st.session_state.step_idx > 0:
                st.session_state.step_idx -= 1
        with step_col3:
            if st.button("下一张 ▶") and st.session_state.step_idx < len(steps) - 1:
                st.session_state.step_idx += 1

        # 当前步骤详情
        current_step = steps[st.session_state.step_idx]

        # 显示截图
        screenshot_file = current_step.get("screenshot_file", "")
        if screenshot_file:
            screenshot_path = task_dir / screenshot_file
            if screenshot_path.exists():
                st.image(str(screenshot_path), caption=f"第 {st.session_state.step_idx + 1} 步截图", width=800)
            else:
                st.warning(f"⚠️ 截图文件不存在: {screenshot_path}")

        # 显示动作信息
        action = current_step.get("action", {})
        if isinstance(action, dict):
            action_type = action.get("input", {}).get("action", "未知")
            action_args = action.get("input", {})
            st.markdown(f"**动作类型:** `{action_type}`")

            # 坐标信息
            coord = action_args.get("coordinate", [])
            if coord:
                st.markdown(f"**点击坐标:** {coord}")

            # 文本输入
            text = action_args.get("text", "")
            if text:
                st.markdown(f"**输入文本:** `{text[:100]}{'...' if len(text) > 100 else ''}`")

            # 推理过程
            command = action.get("command", "")
            if command and len(command) > 10:
                # 简单检查是否有失败相关关键词
                detected, kw = check_if_agent_detected_failure(current_step)
                if detected:
                    st.success(f"🔍 **智能体可能意识到问题：** {kw}")
                st.markdown("**智能体思考过程:**")
                st.code(command[:500] + ("..." if len(command) > 500 else ""))
        else:
            st.markdown(f"**动作:** {action}")

        # 反馈信息
        reward = current_step.get("reward", 0)
        done = current_step.get("done", False)
        st.markdown(f"**Reward:** {reward} | **Done:** {done}")

        # ========== 标注表单 ==========
        st.markdown("---")
        st.subheader("✏️ 标注")

        with st.form(key="annotation_form"):
            st.markdown("**请选择这条轨迹的主要失败类型：**")

            # 简化选项
            selected_type = st.radio(
                "失败类型：",
                options=list(FAILURE_TYPES.keys()),
                format_func=lambda x: x,
                label_visibility="collapsed"
            )

            # 显示选中类型的说明
            st.info(FAILURE_TYPES[selected_type])

            # 额外信息
            col_first, col_detect = st.columns(2)
            with col_first:
                first_fail_step = st.number_input(
                    "第一步出错在第几步？（从1开始）",
                    min_value=1,
                    max_value=len(steps),
                    value=1,
                    help="指出轨迹中第一个实质性错误出现在哪一步"
                )

            with col_detect:
                agent_detected = st.radio(
                    "智能体是否察觉到出错？",
                    options=["是", "否", "不确定"],
                    horizontal=True
                )

            # 备注
            notes = st.text_area(
                "备注（可选）",
                placeholder="任何你觉得需要记录的内容...",
                height=80
            )

            st.markdown("---")

            col_sub1, col_sub2 = st.columns([1, 4])
            with col_sub1:
                submitted = st.form_submit_button("✅ 提交标注", type="primary", use_container_width=True)
            with col_sub2:
                skip_submitted = st.form_submit_button("⏭️ 跳过这条（无法确定）", use_container_width=True)

            if submitted or skip_submitted:
                if skip_submitted:
                    selected_type = "跳过-无法确定"

                annotation = {
                    "trajectory_id": traj_id,
                    "task_id": traj["task_id"],
                    "total_steps": len(steps),
                    "first_failure_step": first_fail_step if selected_type != "无失败" else 0,
                    "failure_type": selected_type,
                    "agent_detected": agent_detected,
                    "notes": notes,
                    "annotated_at": str(Path.cwd()),
                }

                save_annotation(annotation)
                st.session_state.annotated.add(traj_id)
                st.success(f"✅ 已保存标注：{selected_type}")

                # 自动跳到下一条
                if st.session_state.current_idx < len(unannotated) - 1:
                    st.session_state.current_idx += 1
                    st.session_state.step_idx = 0
                    st.rerun()
                else:
                    st.balloons()
                    st.info("🎉 所有轨迹都标注完成了！")

# 底部说明
st.markdown("---")
st.markdown("""
**标注说明：**
- 🎯 仔细查看每一张截图，理解智能体在做什么
- 🤔 注意智能体的"思考过程"（灰色代码区域），看它是否意识到自己出错
- ⏭️ 如果无法确定，可以跳过
""")
