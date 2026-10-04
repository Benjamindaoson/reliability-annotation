"""
Tests for Annotation Schema
"""

import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema import (
    AnnotationRecord, AnnotatorType, FailureType,
    AgentDetected, RecoveryStatus, read_annotations, write_annotations
)


class TestAnnotationRecord:
    """Test AnnotationRecord class"""

    def test_create_basic_record(self):
        """Test creating a basic annotation record"""
        record = AnnotationRecord(
            trajectory_id="test_001",
            annotator_id="claude",
            annotator_model="claude-3-5-sonnet",
            annotator_type=AnnotatorType.LLM,
            failure_type=FailureType.RECOGNITION,
            confidence=0.8
        )

        assert record.trajectory_id == "test_001"
        assert record.annotator_type == AnnotatorType.LLM
        assert record.failure_type == FailureType.RECOGNITION
        assert record.confidence == 0.8

    def test_to_dict_conversion(self):
        """Test conversion to dictionary"""
        record = AnnotationRecord(
            trajectory_id="test_001",
            annotator_id="claude",
            annotator_model="claude-3-5-sonnet",
            annotator_type=AnnotatorType.LLM,
            failure_type=FailureType.SELECTION,
            confidence=0.9,
            first_consequential_failure_step=2
        )

        d = record.to_dict()

        assert d["trajectory_id"] == "test_001"
        assert d["annotator_type"] == "LLM"
        assert d["failure_type"] == "SELECTION"
        assert d["first_consequential_failure_step"] == 2
        # Enum values should be strings
        assert isinstance(d["annotator_type"], str)
        assert isinstance(d["failure_type"], str)

    def test_round_trip(self):
        """Test JSON serialization and deserialization"""
        record = AnnotationRecord(
            trajectory_id="test_001",
            annotator_id="claude",
            annotator_model="claude-3-5-sonnet",
            annotator_type=AnnotatorType.LLM,
            failure_type=FailureType.RECOGNITION,
            confidence=0.85,
            first_consequential_failure_step=3,
            agent_detected_failure=AgentDetected.NO,
            evidence_steps=[3, 4, 5],
            evidence_text="At step 3, the agent clicked the wrong button"
        )

        # Convert to JSON and back
        json_str = record.to_json()
        restored = AnnotationRecord.from_json(json_str)

        assert restored.trajectory_id == record.trajectory_id
        assert restored.failure_type == record.failure_type
        assert restored.confidence == record.confidence
        assert restored.first_consequential_failure_step == record.first_consequential_failure_step
        assert restored.agent_detected_failure == record.agent_detected_failure
        assert restored.evidence_steps == record.evidence_steps

    def test_validation_valid(self):
        """Test validation with valid record"""
        record = AnnotationRecord(
            trajectory_id="test_001",
            annotator_id="claude",
            annotator_model="claude-3-5-sonnet",
            annotator_type=AnnotatorType.LLM,
            confidence=0.8
        )

        is_valid, errors = record.validate()
        assert is_valid
        assert len(errors) == 0

    def test_validation_invalid_confidence(self):
        """Test validation with invalid confidence"""
        record = AnnotationRecord(
            trajectory_id="test_001",
            annotator_id="claude",
            annotator_model="claude-3-5-sonnet",
            annotator_type=AnnotatorType.LLM,
            confidence=1.5  # Invalid: > 1.0
        )

        is_valid, errors = record.validate()
        assert not is_valid
        assert any("confidence" in e for e in errors)

    def test_validation_missing_required(self):
        """Test validation with missing required fields"""
        record = AnnotationRecord(
            trajectory_id="",  # Empty required field
            annotator_id="claude",
            annotator_model="claude-3-5-sonnet",
            annotator_type=AnnotatorType.LLM
        )

        is_valid, errors = record.validate()
        assert not is_valid
        assert any("trajectory_id" in e for e in errors)

    def test_provenance_fields(self):
        """Test annotation provenance fields"""
        record = AnnotationRecord(
            trajectory_id="test_001",
            annotator_id="claude",
            annotator_model="claude-3-5-sonnet-20241022",
            annotator_type=AnnotatorType.LLM,
            trajectory_hash="abc123",
            annotation_source="api_call",
            prompt_version="v2",
            guideline_version="v1",
            temperature=0.7,
            model_snapshot="snapshot-2024-10-22"
        )

        d = record.to_dict()
        assert d["trajectory_hash"] == "abc123"
        assert d["annotation_source"] == "api_call"
        assert d["prompt_version"] == "v2"
        assert d["temperature"] == 0.7


class TestEnums:
    """Test enum values"""

    def test_failure_types(self):
        """Test all failure types are valid"""
        assert FailureType.SELECTION.value == "SELECTION"
        assert FailureType.EXECUTION.value == "EXECUTION"
        assert FailureType.RECOGNITION.value == "RECOGNITION"
        assert FailureType.RECOVERY.value == "RECOVERY"
        assert FailureType.UNCERTAIN.value == "UNCERTAIN"

    def test_annotator_types(self):
        """Test all annotator types"""
        assert AnnotatorType.HUMAN.value == "HUMAN"
        assert AnnotatorType.LLM.value == "LLM"
        assert AnnotatorType.HEURISTIC.value == "HEURISTIC"

    def test_agent_detected(self):
        """Test agent detected values"""
        assert AgentDetected.YES.value == "YES"
        assert AgentDetected.NO.value == "NO"
        assert AgentDetected.UNCLEAR.value == "UNCLEAR"

    def test_recovery_status(self):
        """Test recovery status values"""
        assert RecoveryStatus.SUCCESS.value == "SUCCESS"
        assert RecoveryStatus.FAILED.value == "FAILED"
        assert RecoveryStatus.NONE.value == "NONE"
        assert RecoveryStatus.UNKNOWN.value == "UNKNOWN"


class TestFileIO:
    """Test file I/O operations"""

    def test_write_and_read_annotations(self, tmp_path):
        """Test writing and reading annotations"""
        records = [
            AnnotationRecord(
                trajectory_id="test_001",
                annotator_id="claude",
                annotator_model="claude-3-5-sonnet",
                annotator_type=AnnotatorType.LLM,
                failure_type=FailureType.RECOGNITION,
                confidence=0.8
            ),
            AnnotationRecord(
                trajectory_id="test_002",
                annotator_id="gpt",
                annotator_model="gpt-4o",
                annotator_type=AnnotatorType.LLM,
                failure_type=FailureType.SELECTION,
                confidence=0.9
            )
        ]

        # Write
        file_path = tmp_path / "annotations.jsonl"
        write_annotations(records, str(file_path))

        # Read
        read_records = read_annotations(str(file_path))

        assert len(read_records) == 2
        assert read_records[0].trajectory_id == "test_001"
        assert read_records[1].trajectory_id == "test_002"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
