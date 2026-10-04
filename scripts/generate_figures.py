"""
生成论文图表
"""

import json
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

DATA_DIR = Path("data/external/osworld_verified/claude-4-sonnet-15steps/claude-4-sonnet-20250514-15steps")
ANNOTATION_FILE = Path("data/human_annotations/auto_annotations.jsonl")
OUTPUT_DIR = Path("results/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_annotations():
    with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def plot_rq1_overall(annotations, filename="rq1_overall.png"):
    """RQ1: 失败类型总体分布"""
    failure_counts = Counter(a['failure_type'] for a in annotations)

    labels = ['RECOGNITION\n(Undetected)', 'RECOVERY\n(Detected but Failed)', 'SELECTION\n(Wrong Action)']
    sizes = [failure_counts.get('RECOGNITION', 0),
             failure_counts.get('RECOVERY', 0),
             failure_counts.get('SELECTION', 0)]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    explode = (0.05, 0, 0)

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                       autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})

    for autotext in autotexts:
        autotext.set_fontsize(14)
        autotext.set_fontweight('bold')

    ax.set_title('Figure 1: Failure Type Distribution\n(N=361 trajectories)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / filename}")


def plot_rq1_by_task(annotations, filename="rq1_by_task.png"):
    """RQ1: 按任务类型的失败分布"""
    task_types = sorted(set(a['task_type'] for a in annotations))

    # 准备数据
    selection = []
    recognition = []
    recovery = []

    for tt in task_types:
        tt_anns = [a for a in annotations if a['task_type'] == tt]
        n = len(tt_anns)
        if n > 0:
            selection.append(Counter(a['failure_type'] for a in tt_anns).get('SELECTION', 0) / n * 100)
            recognition.append(Counter(a['failure_type'] for a in tt_anns).get('RECOGNITION', 0) / n * 100)
            recovery.append(Counter(a['failure_type'] for a in tt_anns).get('RECOVERY', 0) / n * 100)
        else:
            selection.append(0)
            recognition.append(0)
            recovery.append(0)

    x = range(len(task_types))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 7))
    bars1 = ax.bar([i - width for i in x], selection, width, label='SELECTION', color='#45B7D1')
    bars2 = ax.bar(x, recognition, width, label='RECOGNITION', color='#FF6B6B')
    bars3 = ax.bar([i + width for i in x], recovery, width, label='RECOVERY', color='#4ECDC4')

    ax.set_ylabel('Percentage (%)', fontsize=12)
    ax.set_xlabel('Task Type', fontsize=12)
    ax.set_title('Figure 2: Failure Type Distribution by Task Type', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(task_types, rotation=45, ha='right', fontsize=10)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 100)

    # 添加数值标签
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 10:
                ax.annotate(f'{height:.0f}%',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / filename}")


def plot_rq2_detection_rate(annotations, filename="rq2_detection_rate.png"):
    """RQ2: 各任务类型的检测率"""
    task_types = sorted(set(a['task_type'] for a in annotations))

    detection_rates = []
    undetected_rates = []

    for tt in task_types:
        tt_anns = [a for a in annotations if a['task_type'] == tt]
        n = len(tt_anns)
        if n > 0:
            detect = Counter(a['failure_type'] for a in tt_anns).get('RECOVERY', 0) / n * 100
            undetect = Counter(a['failure_type'] for a in tt_anns).get('RECOGNITION', 0) / n * 100
            detection_rates.append(detect)
            undetected_rates.append(undetect)
        else:
            detection_rates.append(0)
            undetected_rates.append(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(task_types))
    width = 0.35

    bars1 = ax.bar([i - width/2 for i in x], detection_rates, width, label='Detected (RECOVERY)', color='#4ECDC4')
    bars2 = ax.bar([i + width/2 for i in x], undetected_rates, width, label='Undetected (RECOGNITION)', color='#FF6B6B')

    ax.set_ylabel('Percentage (%)', fontsize=12)
    ax.set_xlabel('Task Type', fontsize=12)
    ax.set_title('Figure 3: Agent Failure Detection Rate by Task Type', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(task_types, rotation=45, ha='right', fontsize=10)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 100)

    # 添加平均线
    avg_detect = sum(detection_rates) / len(detection_rates)
    ax.axhline(y=avg_detect, color='#4ECDC4', linestyle='--', alpha=0.7, label=f'Avg Detection: {avg_detect:.1f}%')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / filename}")


def plot_rq3_bottleneck_headroom(annotations, filename="rq3_bottleneck_headroom.png"):
    """RQ3: 瓶颈改善空间分析"""
    failure_counts = Counter(a['failure_type'] for a in annotations)
    total = len(annotations)

    # 计算每种瓶颈的"改善潜力"
    # 如果移除 RECOGNITION 瓶颈，预计能修复 68.7% 的失败
    # 如果移除 RECOVERY 瓶颈，预计能修复 20.8% 的失败
    # 如果移除 SELECTION 瓶颈，预计能修复 10.5% 的失败

    bottleneck_names = ['RECOGNITION\n(Failure Detection)', 'RECOVERY\n(Recovery Strategy)', 'SELECTION\n(Action Selection)']
    percentages = [
        failure_counts.get('RECOGNITION', 0) / total * 100,
        failure_counts.get('RECOVERY', 0) / total * 100,
        failure_counts.get('SELECTION', 0) / total * 100
    ]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(bottleneck_names, percentages, color=colors, edgecolor='black', linewidth=1.2)

    ax.set_ylabel('Percentage of Trajectories (%)', fontsize=12)
    ax.set_xlabel('Bottleneck Type', fontsize=12)
    ax.set_title('Figure 4: Bottleneck Headroom - Potential Improvement by Removing Each Bottleneck',
                 fontsize=14, fontweight='bold')
    ax.set_ylim(0, 80)

    # 添加数值标签
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        ax.annotate(f'{pct:.1f}%',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / filename}")


def main():
    print("=" * 60)
    print("Generating Figures for Paper 1")
    print("=" * 60)

    annotations = load_annotations()
    print(f"\nLoaded {len(annotations)} annotations")

    print("\nGenerating figures...")
    plot_rq1_overall(annotations)
    plot_rq1_by_task(annotations)
    plot_rq2_detection_rate(annotations)
    plot_rq3_bottleneck_headroom(annotations)

    print(f"\nAll figures saved to: {OUTPUT_DIR}/")
    print("\nGenerated files:")
    for f in OUTPUT_DIR.iterdir():
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
