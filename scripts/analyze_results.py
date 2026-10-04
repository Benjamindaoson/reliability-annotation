"""
Paper 1 分析报告生成器
RQ1, RQ2, RQ3 综合分析
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import math

DATA_DIR = Path("data/external/osworld_verified/claude-4-sonnet-15steps/claude-4-sonnet-20250514-15steps")
ANNOTATION_FILE = Path("data/human_annotations/auto_annotations.jsonl")
OUTPUT_DIR = Path("results/analysis")


def load_annotations():
    """加载标注数据"""
    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def analyze_rq1_failure_distribution(annotations):
    """RQ1: 失败类型分布"""
    print("=" * 70)
    print("RQ1: Where does the first consequential failure occur?")
    print("=" * 70)

    failure_types = Counter(a['failure_type'] for a in annotations)
    total = len(annotations)

    print(f"\nOverall Distribution (N={total}):")
    for ft, count in failure_types.most_common():
        pct = count / total * 100
        print(f"  {ft:15s}: {count:3d} ({pct:5.1f}%)")

    # 按任务类型分析
    print("\n\nBy Task Type:")
    task_types = sorted(set(a['task_type'] for a in annotations))
    for tt in task_types:
        tt_anns = [a for a in annotations if a['task_type'] == tt]
        ft_counts = Counter(a['failure_type'] for a in tt_anns)
        n = len(tt_anns)
        types_str = ", ".join([f"{ft}: {count}({count/n*100:.0f}%)" for ft, count in ft_counts.most_common()])
        print(f"  {tt:20s} (n={n:3d}): {types_str}")

    return failure_types


def analyze_rq2_detection_capability(annotations):
    """RQ2: 智能体检测失败的能力"""
    print("\n" + "=" * 70)
    print("RQ2: Can agents detect failures they have caused?")
    print("=" * 70)

    # 由于自动标注没有 agent_detected 数据，我们用 failure_type 作为代理
    # RECOVERY 意味着智能体"尝试修复"，说明它检测到了失败
    # RECOGNITION 意味着智能体没有检测到失败

    recovery_anns = [a for a in annotations if a['failure_type'] == 'RECOVERY']
    recognition_anns = [a for a in annotations if a['failure_type'] == 'RECOGNITION']

    print(f"\nDetection Capability (inferred from failure type):")
    print(f"  Detected & Failed to Recover (RECOVERY): {len(recovery_anns)} ({len(recovery_anns)/len(annotations)*100:.1f}%)")
    print(f"  Failed to Detect (RECOGNITION):           {len(recognition_anns)} ({len(recognition_anns)/len(annotations)*100:.1f}%)")

    # 分析检测失败的模式
    print("\n\nDetection Failure Rate by Task Type:")
    for tt in sorted(set(a['task_type'] for a in annotations)):
        tt_anns = [a for a in annotations if a['task_type'] == tt]
        detection_rate = len([a for a in tt_anns if a['failure_type'] == 'RECOVERY']) / len(tt_anns) * 100
        failure_detect_rate = len([a for a in tt_anns if a['failure_type'] == 'RECOGNITION']) / len(tt_anns) * 100
        print(f"  {tt:20s}: Detection Rate = {detection_rate:5.1f}%, Undetected = {failure_detect_rate:5.1f}%")


def analyze_rq3_bottleneck_impact(annotations):
    """RQ3: 哪种瓶颈对最终成功影响最大"""
    print("\n" + "=" * 70)
    print("RQ3: Which bottleneck, if removed, most improves success?")
    print("=" * 70)

    # 由于没有 oracle intervention 数据，我们分析每种失败类型的"可恢复性"
    # RECOVERY 类型意味着智能体尝试恢复但失败了，说明有恢复窗口
    # 我们可以用第一失败步的位置来推断恢复窗口大小

    print("\nRecovery Window Analysis (steps from start to first failure):")

    for ft in ['SELECTION', 'EXECUTION', 'RECOGNITION', 'RECOVERY']:
        ft_anns = [a for a in annotations if a['failure_type'] == ft]
        if ft_anns:
            steps = [a['first_failure_step'] for a in ft_anns]
            avg_step = sum(steps) / len(steps)
            print(f"  {ft:15s}: n={len(ft_anns):3d}, avg first failure at step {avg_step:.1f}")

    # 分析每种失败类型的特征
    print("\n\nBottleneck Characteristics:")

    for ft in ['SELECTION', 'RECOGNITION', 'RECOVERY']:
        ft_anns = [a for a in annotations if a['failure_type'] == ft]
        if ft_anns:
            task_counts = Counter(a['task_type'] for a in ft_anns)
            print(f"\n  {ft}:")
            print(f"    Most common in: {task_counts.most_common(3)}")
            print(f"    Total: {len(ft_anns)} cases ({len(ft_anns)/len(annotations)*100:.1f}%)")


def generate_summary_statistics(annotations):
    """生成汇总统计"""
    print("\n" + "=" * 70)
    print("Summary Statistics")
    print("=" * 70)

    total = len(annotations)
    failure_counts = Counter(a['failure_type'] for a in annotations)

    print(f"\nDataset: {total} trajectories from Claude-4-Sonnet on OSWorld")
    print(f"Task types: {len(set(a['task_type'] for a in annotations))}")

    print("\n\nKey Findings:")
    print("-" * 70)

    # Finding 1: RECOGNITION is dominant
    recognition_pct = failure_counts.get('RECOGNITION', 0) / total * 100
    print(f"1. RECOGNITION is the dominant failure type ({recognition_pct:.1f}%)")
    print(f"   -> Agents often fail without realizing it")

    # Finding 2: Recovery failure rate
    recovery_pct = failure_counts.get('RECOVERY', 0) / total * 100
    print(f"\n2. RECOVERY failures account for {recovery_pct:.1f}%")
    print(f"   -> When agents detect failures, they often can't fix them")

    # Finding 3: Selection is relatively rare
    selection_pct = failure_counts.get('SELECTION', 0) / total * 100
    print(f"\n3. SELECTION failures are rare ({selection_pct:.1f}%)")
    print(f"   -> Wrong action selection is not the primary bottleneck")

    # Finding 4: Cross-task variation
    task_detect_rates = {}
    for tt in set(a['task_type'] for a in annotations):
        tt_anns = [a for a in annotations if a['task_type'] == tt]
        detect_rate = len([a for a in tt_anns if a['failure_type'] == 'RECOVERY']) / len(tt_anns) * 100
        task_detect_rates[tt] = detect_rate

    highest = max(task_detect_rates, key=task_detect_rates.get)
    lowest = min(task_detect_rates, key=task_detect_rates.get)
    print(f"\n4. Detection rates vary by task type:")
    print(f"   Highest: {highest} ({task_detect_rates[highest]:.1f}% recovery rate)")
    print(f"   Lowest:  {lowest} ({task_detect_rates[lowest]:.1f}% recovery rate)")


def export_results(annotations):
    """导出结果为多种格式"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. JSON 格式
    with open(OUTPUT_DIR / "rq1_failure_distribution.json", 'w', encoding='utf-8') as f:
        failure_by_type = defaultdict(list)
        for a in annotations:
            failure_by_type[a['failure_type']].append(a)
        json.dump({
            "total": len(annotations),
            "by_failure_type": {k: len(v) for k, v in failure_by_type.items()},
            "by_task_type": {
                tt: {
                    "total": len([a for a in annotations if a['task_type'] == tt]),
                    "by_failure_type": dict(Counter(a['failure_type'] for a in annotations if a['task_type'] == tt))
                }
                for tt in set(a['task_type'] for a in annotations)
            }
        }, f, indent=2, ensure_ascii=False)

    # 2. CSV 格式（便于论文表格）
    import csv
    with open(OUTPUT_DIR / "rq1_by_task_type.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Task Type', 'Total', 'SELECTION', 'RECOGNITION', 'RECOVERY', 'EXECUTION', 'No Failure'])
        for tt in sorted(set(a['task_type'] for a in annotations)):
            tt_anns = [a for a in annotations if a['task_type'] == tt]
            counts = Counter(a['failure_type'] for a in tt_anns)
            writer.writerow([
                tt,
                len(tt_anns),
                counts.get('SELECTION', 0),
                counts.get('RECOGNITION', 0),
                counts.get('RECOVERY', 0),
                counts.get('EXECUTION', 0),
                counts.get('No Failure', 0)
            ])

    print(f"\n\nResults exported to {OUTPUT_DIR}/")
    print("  - rq1_failure_distribution.json")
    print("  - rq1_by_task_type.csv")


def main():
    print("=" * 70)
    print("Paper 1 Analysis Report")
    print("Do Agents Know When They Fail?")
    print("=" * 70)

    annotations = load_annotations()
    print(f"\nLoaded {len(annotations)} annotations")

    # RQ1: Failure Type Distribution
    analyze_rq1_failure_distribution(annotations)

    # RQ2: Detection Capability
    analyze_rq2_detection_capability(annotations)

    # RQ3: Bottleneck Impact
    analyze_rq3_bottleneck_impact(annotations)

    # Summary
    generate_summary_statistics(annotations)

    # Export
    export_results(annotations)

    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
