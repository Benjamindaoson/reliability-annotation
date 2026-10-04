"""
Annotation Schema v3 for Paper 1
Do Agents Know When They Fail?

A causal decomposition of execution reliability in long-horizon Computer-Use Agents.

Schema v3 Changes from v1:
- Recognition and Recovery are no longer primary failure mechanisms
- Added has_consequential_failure as gate question
- Added failure_recognized as downstream variable
- Added recovery_outcome with PARTIAL option
- Added causal_analysis and evidence_steps
- All temporal fields now use integer steps
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Literal
import json
import hashlib


class AnnotatorType(Enum):
    """Type of annotator"""
    HUMAN = "HUMAN"
    LLM = "LLM"
    HEURISTIC = "HEURISTIC"


# =============================================================================
# A. Consequential Failure Gate
# =============================================================================

class HasConsequentialFailure(Enum):
    """
    Gate question: Did a consequential failure occur?

    YES: At least one failure event that plausibly altered trajectory or outcome
    NO: No consequential failure observed
    UNCLEAR: Cannot determine with confidence
    """
    YES = "YES"
    NO = "NO"
    UNCLEAR = "UNCLEAR"


class FirstFailureMechanism(Enum):
    """
    The mechanism of the FIRST consequential failure.

    This is NOT the same as the old "failure_type".
    Recognition and Recovery are analyzed separately as downstream variables.

    SELECTION: Agent selected the WRONG action given available information.
               Example: Should open file A, but opens file B instead.
               Chinese: "AI 选错了要做的事情"

    EXECUTION: Agent's intended action was correct, but execution failed.
               Example: Correctly decides to save, but clicks wrong position or app doesn't respond.
               Chinese: "AI 想做的事情是对的，但没有正确执行成功"

    UNCERTAIN: Cannot determine mechanism with confidence
    NONE: No consequential failure (see has_consequential_failure)
    """
    SELECTION = "SELECTION"
    EXECUTION = "EXECUTION"
    UNCERTAIN = "UNCERTAIN"
    NONE = "NONE"


# =============================================================================
# B. Failure Recognition (Downstream Variable)
# =============================================================================

class FailureRecognized(Enum):
    """
    After the consequential failure occurred, did the agent become aware of it?

    This is a DOWNSTREAM variable - it presupposes that a failure already occurred.

    YES: Agent explicitly or implicitly acknowledged the failure
    NO: Agent did not recognize the failure and continued as if nothing was wrong
    UNCLEAR: Cannot determine from available evidence
    """
    YES = "YES"
    NO = "NO"
    UNCLEAR = "UNCLEAR"


class RecognitionFailure(Enum):
    """
    Did the agent FAIL to recognize a failure that it had reasonable opportunity to observe?

    This is true when:
    1. A consequential failure occurred
    2. The agent had reasonable opportunity to observe the anomaly
    3. The agent did NOT recognize the failure

    YES: Recognition failure occurred (failure went unnoticed)
    NO: No recognition failure (agent noticed or had no opportunity)
    UNCLEAR: Cannot determine
    """
    YES = "YES"
    NO = "NO"
    UNCLEAR = "UNCLEAR"


# =============================================================================
# C. Recovery (Independent Component)
# =============================================================================

class RecoveryAttempted(Enum):
    """
    Did the agent attempt to recover from the failure?

    Only applicable after a failure has occurred.

    YES: Agent attempted some form of recovery
    NO: Agent did not attempt recovery
    UNCLEAR: Cannot determine
    """
    YES = "YES"
    NO = "NO"
    UNCLEAR = "UNCLEAR"


class RecoveryOutcome(Enum):
    """
    Outcome of the recovery attempt.

    SUCCESS: Agent successfully recovered and trajectory returned to productive path
    PARTIAL: Some progress made but task still compromised
    FAILED: Recovery attempt failed
    NOT_ATTEMPTED: No recovery was attempted
    UNCLEAR: Cannot determine outcome
    """
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    UNCLEAR = "UNCLEAR"


# =============================================================================
# D. Confidence
# =============================================================================

class ConfidenceLevel(Enum):
    """
    Annotator's confidence in the overall annotation.

    HIGH: Clear evidence, unambiguous
    MEDIUM: Some ambiguity but confident in overall assessment
    LOW: Significant uncertainty
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# =============================================================================
# E. Causal Analysis
# =============================================================================

class CausalPhase(Enum):
    """
    Phases in the failure causal chain.
    """
    ONSET = "onset"           # When the failure first occurred
    PROPAGATION = "propagation"  # How the failure spread
    RECOGNITION = "recognition"  # When/if agent noticed
    RECOVERY = "recovery"        # Recovery attempt and outcome


# =============================================================================
# Main Annotation Record
# =============================================================================

@dataclass
class AnnotationRecordV3:
    """
    Unified annotation record for trajectory failure analysis - Schema v3.

    This schema is designed for multi-annotator validation with:
    - Strict separation of failure onset mechanism vs recognition vs recovery
    - Full traceability of evidence
    - Double-blind Human Gold support

    Annotator Types:
    - HUMAN: Manual human annotation (scientific evidence)
    - LLM: Claude/GPT/Gemini annotation (comparative)
    - HEURISTIC: Rule-based automatic annotation (NOT scientific evidence)
    """

    # =========================================================================
    # Core Identifiers
    # =========================================================================
    trajectory_id: str = ""
    annotator_id: str = ""
    annotator_type: AnnotatorType = AnnotatorType.HUMAN

    # =========================================================================
    # Trajectory Context
    # =========================================================================
    task_type: str = ""
    task_success: Optional[bool] = None  # True/False/None if unclear
    trajectory_hash: str = ""  # SHA256 of task_id + steps

    # =========================================================================
    # A. Failure Onset
    # =========================================================================
    has_consequential_failure: HasConsequentialFailure = HasConsequentialFailure.UNCLEAR

    first_consequential_failure_step: Optional[int] = None
    """The earliest step whose correction would plausibly alter trajectory or outcome"""

    first_failure_mechanism: FirstFailureMechanism = FirstFailureMechanism.NONE
    """
    SELECTION: "AI 选错了要做的事情"
    EXECUTION: "AI 想做对但没做成"
    """

    # =========================================================================
    # B. Failure Recognition
    # =========================================================================
    failure_recognized: FailureRecognized = FailureRecognized.UNCLEAR
    """After failure occurred, did agent become aware?"""

    detection_step: Optional[int] = None
    """Step where agent first appeared to recognize the problem"""

    recognition_failure: RecognitionFailure = RecognitionFailure.UNCLEAR
    """Did agent fail to recognize a failure it should have noticed?"""

    # =========================================================================
    # C. Recovery
    # =========================================================================
    recovery_attempted: RecoveryAttempted = RecoveryAttempted.UNCLEAR
    """Did agent attempt recovery?"""

    recovery_start_step: Optional[int] = None
    """Step where recovery attempt began"""

    recovery_outcome: RecoveryOutcome = RecoveryOutcome.UNCLEAR
    """Outcome of recovery attempt"""

    # =========================================================================
    # D. Evidence
    # =========================================================================
    evidence_steps: list[int] = field(default_factory=list)
    """Steps that support this annotation"""

    causal_analysis: dict = field(default_factory=dict)
    """Narrative analysis keyed by CausalPhase"""

    # =========================================================================
    # E. Confidence
    # =========================================================================
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # =========================================================================
    # F. Traceability
    # =========================================================================
    annotator_notes: str = ""
    schema_version: str = "v3"
    guideline_version: str = "v3"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        """Set timestamps on creation"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        """Convert to dictionary with enum values as strings"""
        d = asdict(self)

        # Convert enums to values
        enum_fields = [
            'annotator_type', 'has_consequential_failure', 'first_failure_mechanism',
            'failure_recognized', 'recognition_failure', 'recovery_attempted',
            'recovery_outcome', 'confidence'
        ]
        for field in enum_fields:
            if field in d and isinstance(d[field], Enum):
                d[field] = d[field].value

        return d

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> 'AnnotationRecordV3':
        """Create from dictionary"""
        # Make a copy to avoid mutating input
        d = dict(d)

        # Convert string values back to enums
        enum_mappings = {
            'annotator_type': AnnotatorType,
            'has_consequential_failure': HasConsequentialFailure,
            'first_failure_mechanism': FirstFailureMechanism,
            'failure_recognized': FailureRecognized,
            'recognition_failure': RecognitionFailure,
            'recovery_attempted': RecoveryAttempted,
            'recovery_outcome': RecoveryOutcome,
            'confidence': ConfidenceLevel,
        }

        for field, enum_class in enum_mappings.items():
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = enum_class(d[field])
                except ValueError:
                    pass  # Keep as string if enum value not found

        return cls(**d)

    @classmethod
    def from_json(cls, json_str: str) -> 'AnnotationRecordV3':
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the annotation record.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Required string fields
        if not self.trajectory_id:
            errors.append("trajectory_id is required")
        if not self.annotator_id:
            errors.append("annotator_id is required")

        # Annotator type
        if not isinstance(self.annotator_type, AnnotatorType):
            errors.append(f"Invalid annotator_type: {self.annotator_type}")

        # Step validation
        if self.first_consequential_failure_step is not None:
            if self.first_consequential_failure_step < 0:
                errors.append(f"first_consequential_failure_step must be non-negative")

        if self.detection_step is not None:
            if self.detection_step < 0:
                errors.append(f"detection_step must be non-negative")

        if self.recovery_start_step is not None:
            if self.recovery_start_step < 0:
                errors.append(f"recovery_start_step must be non-negative")

        # Temporal consistency
        if self.has_consequential_failure == HasConsequentialFailure.YES:
            if self.first_consequential_failure_step is None:
                errors.append("first_consequential_failure_step required when has_consequential_failure=YES")
            if self.first_failure_mechanism == FirstFailureMechanism.NONE:
                errors.append("first_failure_mechanism cannot be NONE when failure occurred")
        else:
            if self.first_consequential_failure_step is not None:
                errors.append("first_consequential_failure_step should be null when no failure")

        return len(errors) == 0, errors

    def compute_trajectory_hash(self, task_id: str, steps_json: str) -> str:
        """Compute hash for trajectory verification"""
        content = f"{task_id}:{steps_json}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


def read_annotations_v3(file_path: str) -> list[AnnotationRecordV3]:
    """Read annotations from JSONL file"""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(AnnotationRecordV3.from_dict(json.loads(line)))
    return records


def write_annotations_v3(records: list[AnnotationRecordV3], file_path: str):
    """Write annotations to JSONL file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')


# =============================================================================
# Schema Version Info
# =============================================================================

SCHEMA_VERSION = "3.0.0"
SCHEMA_DATE = "2026-10-04"
SCHEMA_MIGRATION_NOTE = """
Migration from v1 to v3:
- failure_type (SELECTION/EXECUTION/RECOGNITION/RECOVERY) -> first_failure_mechanism (SELECTION/EXECUTION/UNCERTAIN/NONE)
- RECOGNITION is now analyzed as failure_recognized + recognition_failure (downstream)
- RECOVERY is now independent with recovery_attempted + recovery_outcome
- Added has_consequential_failure gate question
- Added evidence_steps and causal_analysis for traceability
"""


# =============================================================================
# Human-Readable Definitions (for annotation tool)
# =============================================================================

FAILURE_MECHANISM_DEFINITIONS = {
    "SELECTION": {
        "internal": "SELECTION",
        "chinese": "AI 选错了要做的事情",
        "explanation": "AI 的决定本身就是错误的。应该打开文件 A，AI 却决定去打开文件 B。",
        "mnemonic": "想错了",
        "examples": [
            "应该点击'保存'却点击了'取消'",
            "应该编辑文档却打开了错误的应用",
            "应该在浏览器地址栏输入却点击了搜索框"
        ]
    },
    "EXECUTION": {
        "internal": "EXECUTION",
        "chinese": "AI 想做的事情是对的，但没有正确执行成功",
        "explanation": "AI 的目标是对的，但点击、输入、软件响应、命令或执行结果出了问题。",
        "mnemonic": "想对了但没做成",
        "examples": [
            "正确决定保存文件，但点击位置错误",
            "正确输入了命令，但应用没有响应",
            "正确点击了按钮，但点击被系统忽略"
        ]
    }
}

RECOGNITION_DEFINITIONS = {
    "important_note": "系统显示'失败'（Failed），不等于 AI 已经发现失败。",
    "check": "请看 AI 后面说了什么、做了什么，而不仅仅是看系统反馈。"
}

RECOVERY_DEFINITIONS = {
    "outcomes": {
        "SUCCESS": "成功救回来",
        "PARTIAL": "部分救回来",
        "FAILED": "尝试了但失败",
        "NOT_ATTEMPTED": "没有尝试",
        "UNCLEAR": "无法判断"
    }
}
