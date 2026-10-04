"""
OSWorld 轨迹自动标注脚本 v2
基于动作模式分析，无须推理文本

判断逻辑：
1. RECOGNITION: 最终失败 + 没有重试模式 + 没有意识到失败的迹象
2. SELECTION: 点击了明显错误的目标（比如点击了无关区域）
3. EXECUTION: 动作意图正确但坐标/参数错误
4. RECOVERY: 有重试/回退模式但仍然失败
"""

import json
from pathlib import Path
from collections import Counter
import math


DATA_DIR = Path("data/external/osworld_verified/claude-4-sonnet-15steps/claude-4-sonnet-20250514-15steps")
OUTPUT_FILE = Path("data/human_annotations/auto_annotations.jsonl")


def parse_action(action: dict) -> dict:
    """解析动作"""
    if isinstance(action, dict):
        inp = action.get("input", {})
        return {
            "type": inp.get("action", "unknown"),
            "coords": inp.get("coordinate", []),
            "start": inp.get("start_coordinate", []),
            "text": inp.get("text", ""),
            "duration": inp.get("duration", 0),
        }
    return {"type": "unknown", "coords": [], "start": [], "text": "", "duration": 0}


def analyze_action_pattern(steps: list) -> dict:
    """
    分析动作模式，返回特征
    """
    coords = []
    action_types = []
    text_inputs = []
    drags = []

    for s in steps:
        a = parse_action(s.get("action", {}))
        action_types.append(a["type"])
        if a["coords"]:
            coords.append(tuple(a["coords"]))
        if a["text"]:
            text_inputs.append(a["text"])
        if a["start"] and a["coords"]:
            drags.append((tuple(a["start"]), tuple(a["coords"])))

    return {
        "coords": coords,
        "action_types": action_types,
        "text_inputs": text_inputs,
        "drags": drags,
        "total_steps": len(steps),
    }


def detect_retry_pattern(steps: list) -> tuple[bool, int]:
    """
    检测重试模式：是否有类似动作的重复
    返回: (有重试模式, 重试次数)
    """
    coords = []
    for s in steps:
        a = parse_action(s.get("action", {}))
        if a["coords"]:
            coords.append(tuple(a["coords"]))

    if len(coords) < 3:
        return False, 0

    # 检测相似坐标的重复
    retry_count = 0
    for i in range(len(coords) - 1):
        c1 = coords[i]
        c2 = coords[i + 1]
        if c1 and c2:
            dist = math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)
            # 如果两个坐标非常接近（< 20像素），认为是重试
            if dist < 20:
                retry_count += 1

    return retry_count >= 2, retry_count


def detect_random_clicks(steps: list) -> tuple[bool, float]:
    """
    检测随机点击模式：坐标是否在屏幕上随机分布
    返回: (是随机模式, 分散度分数)
    """
    coords = []
    for s in steps:
        a = parse_action(s.get("action", {}))
        if a["coords"] and a["type"] in ["left_click", "right_click", "double_click"]:
            coords.append(tuple(a["coords"]))

    if len(coords) < 3:
        return False, 0.0

    # 计算坐标的方差
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]

    # 如果 x 和 y 的标准差都很大，说明点击很分散
    x_std = (max(xs) - min(xs)) if xs else 0
    y_std = (max(ys) - min(ys)) if ys else 0

    # 假设屏幕是 1920x1080，如果分散度超过 80% 认为是随机的
    spread_score = (x_std / 1920 + y_std / 1080) / 2

    return spread_score > 0.7, spread_score


def detect_wrong_target(clicks: list, task_type: str) -> bool:
    """
    检测是否点击了错误目标
    基于常见错误模式
    """
    if not clicks:
        return False

    # 检测点击是否集中在屏幕边缘（可能是误点）
    edge_clicks = 0
    for c in clicks:
        x, y = c
        # 屏幕边缘区域
        if x < 50 or x > 1800 or y < 50 or y > 1000:
            edge_clicks += 1

    # 如果超过 30% 的点击在边缘，可能是误操作
    if len(clicks) > 0 and edge_clicks / len(clicks) > 0.3:
        return True

    return False


def classify_failure(steps: list, task_type: str) -> tuple[str, str, int]:
    """
    分类失败类型
    返回: (失败类型, 理由, 第一失败步)
    """
    parsed_steps = [parse_action(s.get("action", {})) for s in steps]
    action_types = [p["type"] for p in parsed_steps]
    coords = [p["coords"] for p in parsed_steps]
    rewards = [s.get("reward", 0) for s in steps]
    final_reward = rewards[-1] if rewards else 0

    # 检查最终结果
    if final_reward > 0:
        # 可能成功了，但检查是否有隐含的失败
        # 这里假设成功了就没有失败
        return "无失败", "轨迹最终成功", 0

    # 找到第一个低 reward 的步骤
    first_fail = 0
    for i, r in enumerate(rewards):
        if r < 0:
            first_fail = i
            break
        elif r == 0 and i > 0:  # reward 为 0 但不是第一步，可能是问题
            # 检查这一步是否是合理的
            if parsed_steps[i]["type"] in ["screenshot"]:
                continue
            first_fail = i
            break

    # 分析模式
    has_retry, retry_count = detect_retry_pattern(steps)
    is_random, spread = detect_random_clicks(steps)

    # 统计点击动作
    clicks = [c for c in coords if c]
    has_wrong_target = detect_wrong_target(clicks, task_type)

    # 根据模式分类
    if is_random:
        return "SELECTION", f"点击坐标高度分散（{spread:.2f}），可能选择了错误的目标", first_fail

    if has_wrong_target:
        return "SELECTION", "大量点击在屏幕边缘，可能点击了错误目标", first_fail

    if has_retry:
        return "RECOVERY", f"检测到重试模式（{retry_count}次重复点击），智能体意识到问题但修复失败", first_fail

    # 检查坐标合理性
    for i, c in enumerate(coords):
        if c:
            x, y = c
            # 坐标越界
            if x < 0 or y < 0 or x > 3000 or y > 2000:
                return "EXECUTION", f"坐标越界 ({x}, {y})", i

    # 默认：认为是未察觉失败
    return "RECOGNITION", "未检测到重试或选择错误模式，智能体可能未察觉失败", first_fail


def main():
    print("=" * 60)
    print("OSWorld Trajectory Auto-Annotation v2")
    print("=" * 60)

    # 收集轨迹
    trajectories = []
    for task_type_dir in DATA_DIR.iterdir():
        if not task_type_dir.is_dir():
            continue
        for traj_dir in task_type_dir.iterdir():
            if not traj_dir.is_dir():
                continue
            traj_file = traj_dir / "traj.jsonl"
            if not traj_file.exists():
                continue
            trajectories.append((task_type_dir.name, traj_dir))

    print(f"Found {len(trajectories)} trajectories")
    print()

    # 分析
    results = []
    for i, (task_type, traj_dir) in enumerate(trajectories):
        if (i + 1) % 50 == 0:
            print(f"Processing... {i + 1}/{len(trajectories)}")

        traj_file = traj_dir / "traj.jsonl"
        steps = []
        with open(traj_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    steps.append(json.loads(line))

        if not steps:
            continue

        failure_type, reasoning, first_fail = classify_failure(steps, task_type)
        final_result = "success" if steps[-1].get("reward", 0) > 0 else "failure"

        results.append({
            "trajectory_id": f"{task_type}/{traj_dir.name}",
            "task_id": traj_dir.name,
            "task_type": task_type,
            "total_steps": len(steps),
            "final_result": final_result,
            "first_failure_step": first_fail + 1,
            "failure_type": failure_type,
            "agent_detected": "N/A",  # 无法从动作推断
            "reasoning": reasoning,
            "annotated_by": "auto",
        })

    # 统计
    print(f"\nAnalyzed {len(results)} trajectories")

    type_counts = Counter(r["failure_type"] for r in results)
    result_counts = Counter(r["final_result"] for r in results)

    print()
    print("=" * 60)
    print("Results Summary")
    print("=" * 60)
    print("\nFailure types:")
    for t, c in type_counts.most_common():
        print(f"  {t}: {c} ({c/len(results)*100:.1f}%)")

    print("\nFinal results:")
    for r, c in result_counts.most_common():
        print(f"  {r}: {c} ({c/len(results)*100:.1f}%)")

    # 保存
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f"\nSaved to: {OUTPUT_FILE}")

    # 示例
    print()
    print("=" * 60)
    print("Sample Results")
    print("=" * 60)
    for r in results[:10]:
        print(f"\n{r['trajectory_id']}")
        print(f"  Result: {r['final_result']}")
        print(f"  Failure: {r['failure_type']}")
        print(f"  Reason: {r['reasoning']}")


if __name__ == "__main__":
    main()
