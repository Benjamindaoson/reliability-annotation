"""
Annotation Schema for Paper 1
Do Agents Know When They Fail?

This module defines the unified annotation schema for trajectory failure analysis.
All annotations (human, LLM, or heuristic) must conform to this schema.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class AnnotatorType(Enum):
    """Type of annotator"""
    HUMAN = "HUMAN"
    LLM = "LLM"
    HEURISTIC = "HEURISTIC"


class FailureType(Enum):
    """
    Type of failure (mutually exclusive)

    SELECTION: Agent selected the WRONG action given available information.
    EXECUTION: Correct intended action but environment failed to execute.
    RECOGNITION: Outcome failed but agent did not notice.
    RECOVERY: Agent noticed failure but failed to recover.
    UNCERTAIN: Cannot determine with confidence.
    """
    SELECTION = "SELECTION"
    EXECUTION = "EXECUTION"
    RECOGNITION = "RECOGNITION"
    RECOVERY = "RECOVERY"
    UNCERTAIN = "UNCERTAIN"


class AgentDetected(Enum):
    """Whether the agent detected the failure"""
    YES = "YES"
    NO = "NO"
    UNCLEAR = "UNCLEAR"


class RecoveryStatus(Enum):
    """Status of recovery attempt"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


@dataclass
class AnnotationRecord:
    """
    Unified annotation record for trajectory failure analysis.

    All fields are required unless marked as Optional.

    This schema is designed for multi-annotator validation:
    - HUMAN: Manual human annotation
    - LLM: Claude/Codex/Gemini annotation
    - HEURISTIC: Rule-based automatic annotation (NOT scientific evidence)
    """
    # Core identifiers
    trajectory_id: str
    annotator_id: str
    annotator_model: str
    annotator_type: AnnotatorType

    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Trajectory snapshot hash (sha256 of task_id + steps JSON)
    # Ensures all annotators see the same trajectory version
    trajectory_hash: str = ""

    # Annotation provenance
    annotation_source: str = "manual_import"  # manual_import, api_call, batch_process
    prompt_version: str = "v1"
    guideline_version: str = "v1"
    temperature: Optional[float] = None
    model_snapshot: str = ""

    # Failure information
    first_consequential_failure_step: Optional[int] = None
    failure_type: FailureType = FailureType.UNCERTAIN

    # Confidence (0.0 to 1.0)
    confidence: float = 0.0

    # Agent awareness
    agent_detected_failure: AgentDetected = AgentDetected.UNCLEAR
    detection_step: Optional[int] = None

    # Recovery
    recovery_status: RecoveryStatus = RecoveryStatus.UNKNOWN

    # Evidence (CRITICAL: required for paper evidence)
    evidence_steps: list[int] = field(default_factory=list)
    evidence_text: str = ""
    annotator_notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary with enum values as strings"""
        d = asdict(self)
        d['annotator_type'] = self.annotator_type.value
        d['failure_type'] = self.failure_type.value
        d['agent_detected_failure'] = self.agent_detected_failure.value
        d['recovery_status'] = self.recovery_status.value
        return d

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> 'AnnotationRecord':
        """Create from dictionary"""
        # Convert string values back to enums
        if isinstance(d.get('annotator_type'), str):
            d['annotator_type'] = AnnotatorType(d['annotator_type'])
        if isinstance(d.get('failure_type'), str):
            d['failure_type'] = FailureType(d['failure_type'])
        if isinstance(d.get('agent_detected_failure'), str):
            d['agent_detected_failure'] = AgentDetected(d['agent_detected_failure'])
        if isinstance(d.get('recovery_status'), str):
            d['recovery_status'] = RecoveryStatus(d['recovery_status'])
        return cls(**d)

    @classmethod
    def from_json(cls, json_str: str) -> 'AnnotationRecord':
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
        if not self.annotator_model:
            errors.append("annotator_model is required")

        # Annotator type
        if not isinstance(self.annotator_type, AnnotatorType):
            errors.append(f"Invalid annotator_type: {self.annotator_type}")

        # Failure type
        if not isinstance(self.failure_type, FailureType):
            errors.append(f"Invalid failure_type: {self.failure_type}")

        # Confidence range
        if not 0.0 <= self.confidence <= 1.0:
            errors.append(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        # Step validation
        if self.first_consequential_failure_step is not None:
            if self.first_consequential_failure_step < 0:
                errors.append(f"first_consequential_failure_step must be non-negative, got {self.first_consequential_failure_step}")

        if self.detection_step is not None:
            if self.detection_step < 0:
                errors.append(f"detection_step must be non-negative, got {self.detection_step}")

        return len(errors) == 0, errors


def read_annotations(file_path: str) -> list[AnnotationRecord]:
    """Read annotations from JSONL file"""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(AnnotationRecord.from_dict(json.loads(line)))
    return records


def write_annotations(records: list[AnnotationRecord], file_path: str):
    """Write annotations to JSONL file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')


# Schema version for tracking
SCHEMA_VERSION = "1.0.0"
SCHEMA_DATE = "2026-10-02"
