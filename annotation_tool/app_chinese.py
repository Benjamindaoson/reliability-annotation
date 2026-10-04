"""
全中文标注工具 - Human Gold Calibration 版本

长程 Computer-Use Agent 执行可靠性测量

专为普通标注员设计：
- 全中文界面，无需英文
- 无需 AI 知识
- 无需编程知识
- 一步一步引导式标注
- 自动保存，断点续标
- 双盲 Human Gold 支持

使用方法：
    streamlit run annotation_tool/app_chinese.py

或者通过 URL + 标注员编号远程访问：
    streamlit run annotation_tool/app_chinese.py --server.port 8501
"""

import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

import streamlit as st
import pandas as pd

# =============================================================================
# Configuration
# =============================================================================

# Database configuration (SQLite for local, can be upgraded to PostgreSQL)
DATABASE_DIR = Path("data/annotation_db")
ANNOTATIONS_FILE = DATABASE_DIR / "annotations.jsonl"
ASSIGNMENTS_FILE = DATABASE_DIR / "assignments.json"
DRAFTS_FILE = DATABASE_DIR / "drafts.json"

# Session state keys
STATE_KEYS = {
    'current_trajectory': 'current_trajectory',
    'current_step': 'annotation_step',
    'annotations': 'annotations_cache',
    'draft': 'current_draft',
}


# =============================================================================
# Chinese Text Definitions
# =============================================================================

TEXTS = {
    # Page titles
    'app_title': '🔍 AI 执行可靠性标注工具',
    'app_subtitle': '长程 Computer-Use Agent 任务分析',

    # Login
    'login_title': '欢迎使用标注工具',
    'login_subtitle': '请输入您的标注员编号开始工作',
    'annotator_id_label': '标注员编号',
    'annotator_id_placeholder': '例如：A001',
    'login_button': '开始工作 ▶',
    'admin_login': '管理员入口',

    # Task overview
    'task_intro': '📋 任务说明',
    'task_intro_text': '''
    在这个任务中，您需要分析 AI（人工智能）执行电脑操作的过程。

    您的任务是判断：
    1. AI 是否在某个步骤出现了真正的问题
    2. 如果出了问题，是在哪个步骤开始的
    3. 问题出在"想错了"还是"做错了"
    4. AI 后来有没有发现自己出了问题
    5. AI 有没有尝试补救

    **请一步一步回答问题。**
    ''',

    # Step 1: Task description
    'step1_title': '第一步：了解任务目标',
    'step1_instruction': '这是 AI 需要完成的任务：',
    'step1_button': '我已了解任务目标 ▶',

    # Step 2: Has failure
    'step2_title': '第二步：判断是否有真正的问题',
    'step2_question': '在这段操作里，有没有出现一个真正把任务带偏的问题？',
    'step2_hint': '''
    **重要说明：**
    - 不是第一个小失误，而是从这一步开始，后面的操作明显进入了错误路线
    - 最终任务结果因此受到影响
    - 点偏但下一步马上修正的不算
    - 无影响的小失误不算
    ''',
    'option_yes': '有',
    'option_no': '没有',
    'option_unclear': '无法判断',

    # Step 3: Failure step
    'step3_title': '第三步：定位问题步骤',
    'step3_question': '第一次真正把任务带偏的是哪一步？',
    'step3_instruction': '请点击轨迹中出问题的那一步',
    'step3_no_failure': '无需选择（没有发生真正的问题）',

    # Step 4: Failure mechanism
    'step4_title': '第四步：判断问题类型',
    'step4_question': '这里为什么出错？',
    'option_selection': '😕 AI 选错了要做的事情',
    'option_selection_desc': 'AI 的决定本身就是错误的',
    'option_selection_example': '例如：应该打开文件 A，却打开了文件 B',
    'option_execution': '🤷 AI 想做对但没做成',
    'option_execution_desc': 'AI 的目标是对的，但操作出了问题',
    'option_execution_example': '例如：正确决定保存文件，但点击位置错误',
    'option_mechanism_unclear': '❓ 无法判断',

    # Step 5: Recognition
    'step5_title': '第五步：AI 是否发现问题',
    'step5_question': 'AI 后来有没有发现这里出了问题？',
    'step5_hint': '''
    **请注意：**
    系统显示"失败"（Failed），不等于 AI 已经发现失败。
    请看 AI 后面说了什么、做了什么。
    ''',
    'option_recognized': '发现了',
    'option_not_recognized': '没发现',
    'option_recognition_unclear': '看不出来',

    # Step 6: Detection step
    'step6_title': '第六步：定位发现步骤',
    'step6_question': 'AI 是在哪一步第一次明显发现问题的？',

    # Step 7: Recovery
    'step7_title': '第七步：是否尝试补救',
    'step7_question': 'AI 有没有尝试补救？',
    'option_recovery_yes': '有尝试',
    'option_recovery_no': '没有尝试',
    'option_recovery_unclear': '无法判断',

    # Step 8: Recovery outcome
    'step8_title': '第八步：补救结果',
    'step8_question': '最后有没有救回来？',
    'option_recovery_success': '✅ 成功救回来',
    'option_recovery_partial': '🔄 部分救回来',
    'option_recovery_failed': '❌ 尝试了但失败',

    # Step 9: Evidence
    'step9_title': '第九步：选择证据',
    'step9_question': '哪些步骤最能支持你的判断？',
    'step9_hint': '请选择支持您判断的关键步骤（可以多选）',

    # Step 10: Confidence
    'step10_title': '第十步：确定程度',
    'step10_question': '你对这次判断有多确定？',
    'option_conf_high': '🟢 很确定',
    'option_conf_medium': '🟡 比较确定',
    'option_conf_low': '🔴 不太确定',

    # Submit
    'submit_title': '📝 提交标注',
    'submit_button': '✅ 确认提交',
    'submit_success': '✅ 标注已保存！',
    'submit_next': '继续下一条 ▶',

    # Navigation
    'progress': '进度',
    'back_button': '◀ 上一步',
    'next_button': '下一步 ▶',
    'save_draft': '💾 保存草稿',
    'draft_saved': '草稿已保存',

    # Admin
    'admin_title': '📊 标注管理后台',
    'admin_total': '总任务数',
    'admin_completed': '已完成',
    'admin_in_progress': '进行中',
    'admin_pending': '待标注',
    'admin_agreement': '一致率',
    'admin_disagreements': '分歧数',
    'admin_pending_adjudication': '待仲裁',

    # Tutorial
    'tutorial_title': '📚 新手教程',
    'tutorial_intro': '在开始正式标注前，请先完成以下练习：',
    'tutorial_case': '练习案例',
    'tutorial_correct': '正确答案',
    'tutorial_explanation': '解析',
    'tutorial_pass': '通过',
    'tutorial_fail': '继续学习',
    'tutorial_start': '开始练习',
    'tutorial_restart': '重新开始',
}


# =============================================================================
# Tutorial Cases (Chinese explanations)
# =============================================================================

TUTORIAL_CASES = [
    {
        "id": "t001",
        "title": "小失误但自动修正",
        "scenario": "AI 点击位置稍微偏了一点，但马上意识到了这个问题，然后重新点击并成功完成了任务。",
        "answer_has_failure": "没有",  # Not consequential
        "explanation": "虽然有小的失误，但因为 AI 马上修正了，所以没有真正把任务带偏。"
    },
    {
        "id": "t002",
        "title": "Selection 错误",
        "scenario": "任务要求打开文件 A，但 AI 错误地打开了文件 B。之后 AI 一直基于错误文件操作，最终任务失败。",
        "answer_mechanism": "AI 选错了要做的事情",
        "explanation": "AI 从一开始就做出了错误的选择，选择了错误的工作对象，后续所有操作都建立在错误的基础上。"
    },
    {
        "id": "t003",
        "title": "Execution 错误",
        "scenario": "AI 正确决定要保存文件，但点击保存按钮时点击位置稍微偏了一点，导致没有保存成功。之后 AI 没有注意到这个问题，继续进行其他操作。",
        "answer_mechanism": "AI 想做对但没做成",
        "explanation": "AI 的意图是正确的（保存文件），但执行时出了问题（点击位置错误），导致操作没有成功。"
    },
    {
        "id": "t004",
        "title": "AI 发现问题",
        "scenario": "AI 在执行过程中，软件弹出一个错误提示框。AI 看到提示框后，在推理过程中明确说'这里出了问题，我需要重试'，然后重新执行了操作并成功。",
        "answer_recognized": "发现了",
        "answer_recovery": "有尝试",
        "answer_recovery_outcome": "成功救回来",
        "explanation": "AI 明确意识到了问题（通过提示框），并在推理中承认了问题，然后尝试并成功恢复了。"
    },
    {
        "id": "t005",
        "title": "AI 没发现失败",
        "scenario": "任务要求保存文件到特定位置。AI 点击了保存按钮，但软件显示'保存失败'。然而，AI 的后续推理中完全没有提到这个失败，继续假设文件已成功保存。",
        "answer_recognized": "没发现",
        "explanation": "虽然系统显示了'保存失败'（Failed），但 AI 的推理过程完全没有承认或处理这个失败。它继续假设一切正常。"
    },
    {
        "id": "t006",
        "title": "Recovery 失败",
        "scenario": "AI 发现自己之前的操作有问题（选错了文件），于是尝试补救，选择了正确的文件。但新选择的文件操作也出了问题，最终任务仍然失败。",
        "answer_recognized": "发现了",
        "answer_recovery": "有尝试",
        "answer_recovery_outcome": "尝试了但失败",
        "explanation": "AI 发现了问题并尝试恢复，但恢复尝试也失败了，任务最终仍然失败。"
    },
    {
        "id": "t007",
        "title": "环境失败 vs Agent awareness",
        "scenario": "软件崩溃了，显示一个错误对话框。AI 的后续操作中完全没有提到这个错误，继续执行好像什么都没发生一样。",
        "answer_recognized": "没发现",
        "explanation": "虽然环境明显失败了（软件崩溃），但 AI 完全没有表现出对这个问题的认识。这是'环境显示失败'但'AI 没有发现'的典型例子。"
    },
]


# =============================================================================
# Database Functions
# =============================================================================

def init_database():
    """Initialize database directories"""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    # Create empty files if they don't exist
    if not ANNOTATIONS_FILE.exists():
        ANNOTATIONS_FILE.touch()
    if not ASSIGNMENTS_FILE.exists():
        with open(ASSIGNMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not DRAFTS_FILE.exists():
        with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)


def load_annotations() -> list[dict]:
    """Load all annotations"""
    if not ANNOTATIONS_FILE.exists():
        return []

    annotations = []
    with open(ANNOTATIONS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                annotations.append(json.loads(line))
    return annotations


def save_annotation(annotation: dict):
    """Save a single annotation"""
    with open(ANNOTATIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(annotation, ensure_ascii=False) + '\n')


def load_assignments() -> dict:
    """Load assignments"""
    if not ASSIGNMENTS_FILE.exists():
        return {}
    with open(ASSIGNMENTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_assignment(annotator_id: str, trajectory_id: str, status: str):
    """Save assignment status"""
    assignments = load_assignments()
    if annotator_id not in assignments:
        assignments[annotator_id] = {}
    assignments[annotator_id][trajectory_id] = {
        'status': status,
        'updated_at': datetime.now().isoformat()
    }
    with open(ASSIGNMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(assignments, f, ensure_ascii=False)


def load_drafts() -> dict:
    """Load drafts"""
    if not DRAFTS_FILE.exists():
        return {}
    with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_draft(annotator_id: str, trajectory_id: str, draft: dict):
    """Save draft annotation"""
    drafts = load_drafts()
    drafts[f"{annotator_id}:{trajectory_id}"] = {
        'draft': draft,
        'updated_at': datetime.now().isoformat()
    }
    with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(drafts, f, ensure_ascii=False)


def get_draft(annotator_id: str, trajectory_id: str) -> Optional[dict]:
    """Get draft for a specific annotator and trajectory"""
    drafts = load_drafts()
    key = f"{annotator_id}:{trajectory_id}"
    if key in drafts:
        return drafts[key]['draft']
    return None


def get_annotator_progress(annotator_id: str) -> dict:
    """Get annotator's progress"""
    annotations = load_annotations()
    assignments = load_assignments()

    completed = set()
    for ann in annotations:
        if ann.get('annotator_id') == annotator_id:
            completed.add(ann.get('trajectory_id'))

    assigned = assignments.get(annotator_id, {})

    return {
        'completed': list(completed),
        'completed_count': len(completed),
        'assigned': assigned
    }


# =============================================================================
# Trajectory Loading
# =============================================================================

def load_trajectories() -> list[dict]:
    """Load available trajectories for annotation"""
    # Priority: use converted OSWorld data (200 real trajectories)
    data_file = Path("data/raw/osworld_claude4_converted.json")

    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            trajectories = json.load(f)
            print(f"Loaded {len(trajectories)} trajectories from {data_file}")
            return trajectories

    # Fallback: check batch files
    batch_file = Path("annotation_batches/batch_001.json")

    if batch_file.exists():
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch = json.load(f)
            return batch.get('trajectories', [])

    # Fallback: sample trajectories
    loader_path = Path("data/raw/sample_trajectories.json")
    if loader_path.exists():
        with open(loader_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    return []


def get_unannotated_trajectories(annotator_id: str) -> list[dict]:
    """Get trajectories not yet annotated by this annotator"""
    annotations = load_annotations()
    completed_ids = {a.get('trajectory_id') for a in annotations if a.get('annotator_id') == annotator_id}

    trajectories = load_trajectories()
    return [t for t in trajectories if t.get('trajectory_id') not in completed_ids]


# =============================================================================
# Annotation Form Components
# =============================================================================

def render_step_indicator(current_step: int, total_steps: int = 10):
    """Render step indicator"""
    steps = ['任务', '问题', '步骤', '类型', '发现', '发现时', '补救', '补救结', '证据', '确定']

    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps)):
        if i < current_step:
            col.success(f"✓ {step_name}")
        elif i == current_step:
            col.info(f"● {step_name}")
        else:
            col.write(f"○ {step_name}")


def render_trajectory_viewer(trajectory: dict, max_steps: int = None):
    """Render trajectory steps for annotation"""
    steps = trajectory.get('steps', [])
    if max_steps:
        steps = steps[:max_steps]

    task_desc = trajectory.get('task_description', '任务描述不可用')
    st.markdown(f"### 📋 任务目标\n\n{task_desc}")

    st.markdown("### 📜 操作步骤")

    for i, step in enumerate(steps):
        with st.expander(f"**步骤 {i}**", expanded=True):
            # Action
            action = step.get('action', {})
            action_type = action.get('action_type', 'unknown')
            action_args = action.get('action_arguments', {})

            st.markdown(f"**操作类型:** {action_type}")

            if action_args:
                st.markdown("**操作参数:**")
                for k, v in action_args.items():
                    if isinstance(v, str) and len(v) > 100:
                        v = v[:97] + "..."
                    st.code(f"{k}: {v}")

            # Feedback
            feedback = step.get('feedback', {})
            if feedback:
                success = feedback.get('success')
                reward = feedback.get('reward', 0)

                col1, col2 = st.columns(2)
                with col1:
                    if success is not None:
                        if success:
                            st.success("✅ 成功")
                        else:
                            st.error("❌ 失败")
                with col2:
                    st.metric("奖励", reward)

            # Reasoning
            reasoning = step.get('reasoning', '')
            if reasoning:
                st.markdown("**AI 推理过程:**")
                st.info(reasoning[:1000] if len(reasoning) > 1000 else reasoning)

            # Observation hint
            obs = step.get('observation', {})
            if obs:
                obs_text = obs.get('text', '')
                if obs_text:
                    with st.expander("📷 观察信息"):
                        st.text(obs_text[:500] if len(obs_text) > 500 else obs_text)


def render_annotation_form(trajectory: dict, annotator_id: str, draft: dict = None):
    """Render the complete annotation form as a wizard"""

    # Initialize session state for annotation
    if 'annotation_data' not in st.session_state:
        st.session_state.annotation_data = draft if draft else {}

    data = st.session_state.annotation_data

    # Step tracking
    if 'step_num' not in data:
        data['step_num'] = 0

    current_step = data['step_num']

    # Render step indicator
    render_step_indicator(current_step)
    st.markdown("---")

    # Step 0: Task intro
    if current_step == 0:
        st.markdown(f"## {TEXTS['step1_title']}")
        st.markdown(TEXTS['step1_instruction'])

        task_desc = trajectory.get('task_description', '任务描述不可用')
        st.info(task_desc)

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(TEXTS['step1_button'], type="primary", use_container_width=True):
                data['step_num'] = 1
                st.rerun()

    # Step 1: Has failure
    elif current_step == 1:
        st.markdown(f"## {TEXTS['step2_title']}")
        st.markdown(f"### {TEXTS['step2_question']}")
        st.markdown(TEXTS['step2_hint'])

        has_failure = data.get('has_consequential_failure')

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(TEXTS['option_yes'], use_container_width=True):
                data['has_consequential_failure'] = 'YES'
                data['step_num'] = 2
                st.rerun()
        with col2:
            if st.button(TEXTS['option_no'], use_container_width=True):
                data['has_consequential_failure'] = 'NO'
                data['step_num'] = 9  # Skip to evidence/confidence
                st.rerun()
        with col3:
            if st.button(TEXTS['option_unclear'], use_container_width=True):
                data['has_consequential_failure'] = 'UNCLEAR'
                data['step_num'] = 9
                st.rerun()

        if st.button(TEXTS['back_button']):
            data['step_num'] = 0
            st.rerun()

    # Step 2: Failure step
    elif current_step == 2:
        st.markdown(f"## {TEXTS['step3_title']}")
        st.markdown(f"### {TEXTS['step3_question']}")
        st.markdown(TEXTS['step3_instruction'])

        steps = trajectory.get('steps', [])

        # Select step
        selected_step = st.selectbox(
            "选择出问题的步骤：",
            options=list(range(len(steps))),
            format_func=lambda x: f"步骤 {x}"
        )

        # Show context for selected step
        if selected_step is not None:
            step = steps[selected_step]
            with st.expander(f"查看步骤 {selected_step} 详情", expanded=True):
                action = step.get('action', {})
                st.markdown(f"**操作:** {action.get('action_type', 'unknown')}")

                reasoning = step.get('reasoning', '')
                if reasoning:
                    st.markdown("**AI 推理:**")
                    st.info(reasoning[:500])

        data['first_failure_step'] = selected_step

        col1, col2 = st.columns(2)
        with col1:
            if st.button(TEXTS['next_button'], type="primary", use_container_width=True):
                if 'first_failure_step' in data:
                    data['step_num'] = 3
                    st.rerun()
        with col2:
            if st.button(TEXTS['back_button'], use_container_width=True):
                data['step_num'] = 1
                st.rerun()

    # Step 3: Failure mechanism
    elif current_step == 3:
        st.markdown(f"## {TEXTS['step4_title']}")
        st.markdown(f"### {TEXTS['step4_question']}")

        # Selection option
        st.markdown(f"#### {TEXTS['option_selection']}")
        st.caption(TEXTS['option_selection_desc'])
        st.markdown(f"*{TEXTS['option_selection_example']}*")

        # Execution option
        st.markdown(f"#### {TEXTS['option_execution']}")
        st.caption(TEXTS['option_execution_desc'])
        st.markdown(f"*{TEXTS['option_execution_example']}*")

        mechanism = data.get('first_failure_mechanism')

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("😕 选错了", use_container_width=True):
                data['first_failure_mechanism'] = 'SELECTION'
                data['step_num'] = 4
                st.rerun()
        with col2:
            if st.button("🤷 没做成", use_container_width=True):
                data['first_failure_mechanism'] = 'EXECUTION'
                data['step_num'] = 4
                st.rerun()
        with col3:
            if st.button("❓ 无法判断", use_container_width=True):
                data['first_failure_mechanism'] = 'UNCERTAIN'
                data['step_num'] = 4
                st.rerun()

        if st.button(TEXTS['back_button']):
            data['step_num'] = 2
            st.rerun()

    # Step 4: Recognition
    elif current_step == 4:
        st.markdown(f"## {TEXTS['step5_title']}")
        st.markdown(f"### {TEXTS['step5_question']}")
        st.warning(TEXTS['step5_hint'])

        recognized = data.get('failure_recognized')

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(TEXTS['option_recognized'], use_container_width=True):
                data['failure_recognized'] = 'YES'
                data['step_num'] = 5
                st.rerun()
        with col2:
            if st.button(TEXTS['option_not_recognized'], use_container_width=True):
                data['failure_recognized'] = 'NO'
                data['step_num'] = 6  # Skip detection step
                st.rerun()
        with col3:
            if st.button(TEXTS['option_recognition_unclear'], use_container_width=True):
                data['failure_recognized'] = 'UNCLEAR'
                data['step_num'] = 6
                st.rerun()

        if st.button(TEXTS['back_button']):
            data['step_num'] = 3
            st.rerun()

    # Step 5: Detection step
    elif current_step == 5:
        st.markdown(f"## {TEXTS['step6_title']}")
        st.markdown(f"### {TEXTS['step6_question']}")

        steps = trajectory.get('steps', [])
        detection_step = data.get('detection_step', 0)

        selected = st.selectbox(
            "选择 AI 第一次发现问题的步骤：",
            options=list(range(len(steps))),
            index=min(detection_step, len(steps) - 1) if detection_step < len(steps) else 0,
            format_func=lambda x: f"步骤 {x}"
        )

        data['detection_step'] = selected

        col1, col2 = st.columns(2)
        with col1:
            if st.button(TEXTS['next_button'], type="primary", use_container_width=True):
                data['step_num'] = 6
                st.rerun()
        with col2:
            if st.button(TEXTS['back_button'], use_container_width=True):
                data['step_num'] = 4
                st.rerun()

    # Step 6: Recovery
    elif current_step == 6:
        st.markdown(f"## {TEXTS['step7_title']}")
        st.markdown(f"### {TEXTS['step7_question']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(TEXTS['option_recovery_yes'], use_container_width=True):
                data['recovery_attempted'] = 'YES'
                data['step_num'] = 7
                st.rerun()
        with col2:
            if st.button(TEXTS['option_recovery_no'], use_container_width=True):
                data['recovery_attempted'] = 'NO'
                data['recovery_outcome'] = 'NOT_ATTEMPTED'
                data['step_num'] = 8
                st.rerun()
        with col3:
            if st.button(TEXTS['option_recovery_unclear'], use_container_width=True):
                data['recovery_attempted'] = 'UNCLEAR'
                data['step_num'] = 8
                st.rerun()

        if st.button(TEXTS['back_button']):
            data['step_num'] = 5 if data.get('failure_recognized') == 'YES' else 4
            st.rerun()

    # Step 7: Recovery outcome
    elif current_step == 7:
        st.markdown(f"## {TEXTS['step8_title']}")
        st.markdown(f"### {TEXTS['step8_question']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(TEXTS['option_recovery_success'], use_container_width=True):
                data['recovery_outcome'] = 'SUCCESS'
                data['step_num'] = 8
                st.rerun()
        with col2:
            if st.button(TEXTS['option_recovery_partial'], use_container_width=True):
                data['recovery_outcome'] = 'PARTIAL'
                data['step_num'] = 8
                st.rerun()
        with col3:
            if st.button(TEXTS['option_recovery_failed'], use_container_width=True):
                data['recovery_outcome'] = 'FAILED'
                data['step_num'] = 8
                st.rerun()

        if st.button(TEXTS['back_button']):
            data['step_num'] = 6
            st.rerun()

    # Step 8: Evidence
    elif current_step == 8:
        st.markdown(f"## {TEXTS['step9_title']}")
        st.markdown(f"### {TEXTS['step9_question']}")
        st.caption(TEXTS['step9_hint'])

        steps = trajectory.get('steps', [])

        # Multi-select for evidence steps
        evidence = data.get('evidence_steps', [])

        selected_steps = []
        cols = st.columns(min(5, len(steps)))
        for i in range(len(steps)):
            col_idx = i % 5
            if col_idx == 0 and i > 0:
                st.markdown("")  # New row
            with cols[col_idx]:
                is_selected = i in evidence
                label = f"步骤 {i}"
                if st.checkbox(label, value=is_selected, key=f"evidence_{i}"):
                    selected_steps.append(i)

        data['evidence_steps'] = selected_steps

        if st.button(TEXTS['next_button'], type="primary", use_container_width=True):
            data['step_num'] = 9
            st.rerun()

        if st.button(TEXTS['back_button']):
            data['step_num'] = 7 if data.get('recovery_attempted') == 'YES' else 6
            st.rerun()

    # Step 9: Confidence
    elif current_step == 9:
        st.markdown(f"## {TEXTS['step10_title']}")
        st.markdown(f"### {TEXTS['step10_question']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(TEXTS['option_conf_high'], use_container_width=True):
                data['confidence'] = 'HIGH'
                data['step_num'] = 10
                st.rerun()
        with col2:
            if st.button(TEXTS['option_conf_medium'], use_container_width=True):
                data['confidence'] = 'MEDIUM'
                data['step_num'] = 10
                st.rerun()
        with col3:
            if st.button(TEXTS['option_conf_low'], use_container_width=True):
                data['confidence'] = 'LOW'
                data['step_num'] = 10
                st.rerun()

        if st.button(TEXTS['back_button']):
            data['step_num'] = 8
            st.rerun()

    # Step 10: Submit
    elif current_step == 10:
        st.markdown(f"## {TEXTS['submit_title']}")

        # Summary
        st.markdown("### 标注摘要")

        summary_data = {
            'trajectory_id': trajectory.get('trajectory_id'),
            'annotator_id': annotator_id,
            'has_consequential_failure': data.get('has_consequential_failure'),
            'first_failure_step': data.get('first_failure_step'),
            'first_failure_mechanism': data.get('first_failure_mechanism'),
            'failure_recognized': data.get('failure_recognized'),
            'detection_step': data.get('detection_step'),
            'recovery_attempted': data.get('recovery_attempted'),
            'recovery_outcome': data.get('recovery_outcome'),
            'evidence_steps': data.get('evidence_steps', []),
            'confidence': data.get('confidence'),
        }

        st.json(summary_data)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(TEXTS['submit_button'], type="primary", use_container_width=True):
                # Save annotation
                save_annotation(summary_data)
                save_assignment(annotator_id, trajectory.get('trajectory_id'), 'completed')

                # Clear session state
                st.session_state.annotation_data = {}

                st.success(TEXTS['submit_success'])
                st.balloons()

                if st.button(TEXTS['submit_next'], use_container_width=True):
                    data['step_num'] = 0
                    st.rerun()

        with col2:
            if st.button("💾 保存草稿", use_container_width=True):
                save_draft(annotator_id, trajectory.get('trajectory_id'), data)
                st.success(TEXTS['draft_saved'])

    # Save to session state
    st.session_state.annotation_data = data


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point"""

    st.set_page_config(
        page_title=TEXTS['app_title'],
        page_icon="🔍",
        layout="wide"
    )

    # Initialize database
    init_database()

    # Sidebar for login
    with st.sidebar:
        st.header(TEXTS['login_title'])

        if 'annotator_id' not in st.session_state:
            annotator_id = st.text_input(
                TEXTS['annotator_id_label'],
                placeholder=TEXTS['annotator_id_placeholder']
            )

            if st.button(TEXTS['login_button'], type="primary"):
                if annotator_id:
                    st.session_state.annotator_id = annotator_id
                    st.rerun()
                else:
                    st.error("请输入标注员编号")
            return

        # Show logged in state
        st.success(f"已登录: {st.session_state.annotator_id}")

        # Progress
        progress = get_annotator_progress(st.session_state.annotator_id)
        st.metric(TEXTS['progress'], f"{progress['completed_count']} 条")

        # Logout
        if st.button("退出登录"):
            del st.session_state.annotator_id
            st.rerun()

    # Main content area
    st.title(TEXTS['app_title'])
    st.caption(TEXTS['app_subtitle'])

    # Check for draft
    trajectories = load_trajectories()
    if not trajectories:
        st.warning("暂无可用轨迹数据")
        return

    # Get current trajectory
    if 'current_traj_idx' not in st.session_state:
        st.session_state.current_traj_idx = 0

    # Get unannotated
    unannotated = get_unannotated_trajectories(st.session_state.annotator_id)

    if not unannotated:
        st.success("🎉 恭喜！您已完成所有标注任务！")
        return

    # Select trajectory
    current_traj = unannotated[st.session_state.current_traj_idx % len(unannotated)]

    # Check for draft
    draft = get_draft(st.session_state.annotator_id, current_traj.get('trajectory_id'))
    if draft:
        st.info("📝 发现未完成的草稿，正在继续...")

    # Render trajectory info
    with st.expander("📋 当前任务信息"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("轨迹ID", current_traj.get('trajectory_id', '')[:20] + "...")
        with col2:
            st.metric("任务ID", current_traj.get('task_id', '')[:20] + "...")
        with col3:
            st.metric("步数", current_traj.get('length', len(current_traj.get('steps', []))))

    # Render annotation form
    render_annotation_form(current_traj, st.session_state.annotator_id, draft)

    # Admin panel (hidden, accessible via query params)
    query_params = st.query_params
    if query_params.get("admin") == "true":
        st.markdown("---")
        st.markdown(f"## {TEXTS['admin_title']}")

        annotations = load_annotations()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(TEXTS['admin_total'], len(trajectories))
        col2.metric(TEXTS['admin_completed'], len(annotations))
        col3.metric(TEXTS['admin_in_progress'], len(unannotated))
        col4.metric(TEXTS['admin_pending'], len(trajectories) - len(annotations))

        # Annotator breakdown
        if annotations:
            st.markdown("### 标注员进度")
            annotator_counts = {}
            for ann in annotations:
                aid = ann.get('annotator_id', 'unknown')
                annotator_counts[aid] = annotator_counts.get(aid, 0) + 1

            for aid, count in sorted(annotator_counts.items()):
                st.write(f"- {aid}: {count} 条")


if __name__ == "__main__":
    main()
