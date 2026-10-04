"""
Tests for Annotation Schema v3
"""

import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema_v3 import (
    AnnotationRecordV3, AnnotatorType,
    HasConsequentialFailure, FirstFailureMechanism,
    FailureRecognized, RecognitionFailure,
    RecoveryAttempted, RecoveryOutcome, ConfidenceLevel,
    read_annotations_v3, write_annotations_v3,
    FAILURE_MECHANISM_DEFINITIONS
)


class TestAnnotationRecordV3:
    """Test AnnotationRecordV3 class"""

    def test_create_basic_record(self):
        """Test creating a basic annotation record"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.YES,
            first_failure_mechanism=FirstFailureMechanism.SELECTION
        )

        assert record.trajectory_id == "test_001"
        assert record.annotator_type == AnnotatorType.HUMAN
        assert record.has_consequential_failure == HasConsequentialFailure.YES
        assert record.first_failure_mechanism == FirstFailureMechanism.SELECTION

    def test_full_annotation_flow(self):
        """Test complete annotation workflow"""
        record = AnnotationRecordV3(
            trajectory_id="test_002",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            task_type="libreoffice_writer",
            task_success=False,

            has_consequential_failure=HasConsequentialFailure.YES,
            first_consequential_failure_step=3,
            first_failure_mechanism=FirstFailureMechanism.EXECUTION,

            failure_recognized=FailureRecognized.YES,
            detection_step=5,
            recognition_failure=RecognitionFailure.NO,

            recovery_attempted=RecoveryAttempted.YES,
            recovery_start_step=6,
            recovery_outcome=RecoveryOutcome.SUCCESS,

            evidence_steps=[3, 4, 5, 6],
            confidence=ConfidenceLevel.HIGH
        )

        assert record.has_consequential_failure == HasConsequentialFailure.YES
        assert record.first_failure_mechanism == FirstFailureMechanism.EXECUTION
        assert record.failure_recognized == FailureRecognized.YES
        assert record.recovery_outcome == RecoveryOutcome.SUCCESS

    def test_to_dict_conversion(self):
        """Test conversion to dictionary"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.YES,
            first_failure_mechanism=FirstFailureMechanism.SELECTION,
            first_consequential_failure_step=2
        )

        d = record.to_dict()

        assert d["trajectory_id"] == "test_001"
        assert d["annotator_type"] == "HUMAN"
        assert d["has_consequential_failure"] == "YES"
        assert d["first_failure_mechanism"] == "SELECTION"
        assert d["first_consequential_failure_step"] == 2
        # All enum values should be strings
        assert isinstance(d["annotator_type"], str)
        assert isinstance(d["has_consequential_failure"], str)

    def test_round_trip(self):
        """Test JSON serialization and deserialization"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.YES,
            first_failure_mechanism=FirstFailureMechanism.EXECUTION,
            first_consequential_failure_step=3,
            failure_recognized=FailureRecognized.NO,
            recognition_failure=RecognitionFailure.YES,
            recovery_attempted=RecoveryAttempted.YES,
            recovery_outcome=RecoveryOutcome.FAILED,
            evidence_steps=[3, 4, 5],
            confidence=ConfidenceLevel.MEDIUM,
            annotator_notes="Agent clicked wrong button"
        )

        # Convert to JSON and back
        json_str = record.to_json()
        restored = AnnotationRecordV3.from_json(json_str)

        assert restored.trajectory_id == record.trajectory_id
        assert restored.has_consequential_failure == record.has_consequential_failure
        assert restored.first_failure_mechanism == record.first_failure_mechanism
        assert restored.evidence_steps == record.evidence_steps
        assert restored.confidence == record.confidence

    def test_validation_valid(self):
        """Test validation with valid record"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.YES,
            first_failure_mechanism=FirstFailureMechanism.SELECTION,
            first_consequential_failure_step=2
        )

        is_valid, errors = record.validate()
        assert is_valid
        assert len(errors) == 0

    def test_validation_no_failure(self):
        """Test validation with no failure case"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.NO,
            first_failure_mechanism=FirstFailureMechanism.NONE,
            first_consequential_failure_step=None
        )

        is_valid, errors = record.validate()
        assert is_valid

    def test_validation_inconsistency(self):
        """Test validation catches inconsistencies"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.YES,
            first_failure_mechanism=FirstFailureMechanism.NONE,  # Inconsistent
            first_consequential_failure_step=None  # Should be set
        )

        is_valid, errors = record.validate()
        assert not is_valid
        assert len(errors) > 0


class TestEnumsV3:
    """Test enum values for Schema v3"""

    def test_has_consequential_failure(self):
        """Test HasConsequentialFailure values"""
        assert HasConsequentialFailure.YES.value == "YES"
        assert HasConsequentialFailure.NO.value == "NO"
        assert HasConsequentialFailure.UNCLEAR.value == "UNCLEAR"

    def test_first_failure_mechanism(self):
        """Test FirstFailureMechanism values"""
        assert FirstFailureMechanism.SELECTION.value == "SELECTION"
        assert FirstFailureMechanism.EXECUTION.value == "EXECUTION"
        assert FirstFailureMechanism.UNCERTAIN.value == "UNCERTAIN"
        assert FirstFailureMechanism.NONE.value == "NONE"

    def test_failure_recognized(self):
        """Test FailureRecognized values"""
        assert FailureRecognized.YES.value == "YES"
        assert FailureRecognized.NO.value == "NO"
        assert FailureRecognized.UNCLEAR.value == "UNCLEAR"

    def test_recognition_failure(self):
        """Test RecognitionFailure values"""
        assert RecognitionFailure.YES.value == "YES"
        assert RecognitionFailure.NO.value == "NO"
        assert RecognitionFailure.UNCLEAR.value == "UNCLEAR"

    def test_recovery_attempted(self):
        """Test RecoveryAttempted values"""
        assert RecoveryAttempted.YES.value == "YES"
        assert RecoveryAttempted.NO.value == "NO"
        assert RecoveryAttempted.UNCLEAR.value == "UNCLEAR"

    def test_recovery_outcome(self):
        """Test RecoveryOutcome values"""
        assert RecoveryOutcome.SUCCESS.value == "SUCCESS"
        assert RecoveryOutcome.PARTIAL.value == "PARTIAL"
        assert RecoveryOutcome.FAILED.value == "FAILED"
        assert RecoveryOutcome.NOT_ATTEMPTED.value == "NOT_ATTEMPTED"
        assert RecoveryOutcome.UNCLEAR.value == "UNCLEAR"

    def test_confidence_level(self):
        """Test ConfidenceLevel values"""
        assert ConfidenceLevel.HIGH.value == "HIGH"
        assert ConfidenceLevel.MEDIUM.value == "MEDIUM"
        assert ConfidenceLevel.LOW.value == "LOW"


class TestFileIOV3:
    """Test file I/O operations for Schema v3"""

    def test_write_and_read_annotations(self, tmp_path):
        """Test writing and reading annotations"""
        records = [
            AnnotationRecordV3(
                trajectory_id="test_001",
                annotator_id="A001",
                annotator_type=AnnotatorType.HUMAN,
                has_consequential_failure=HasConsequentialFailure.YES,
                first_failure_mechanism=FirstFailureMechanism.SELECTION,
                first_consequential_failure_step=2,
                confidence=ConfidenceLevel.HIGH
            ),
            AnnotationRecordV3(
                trajectory_id="test_002",
                annotator_id="A002",
                annotator_type=AnnotatorType.HUMAN,
                has_consequential_failure=HasConsequentialFailure.NO,
                first_failure_mechanism=FirstFailureMechanism.NONE,
                confidence=ConfidenceLevel.MEDIUM
            )
        ]

        # Write
        file_path = tmp_path / "annotations_v3.jsonl"
        write_annotations_v3(records, str(file_path))

        # Read
        read_records = read_annotations_v3(str(file_path))

        assert len(read_records) == 2
        assert read_records[0].trajectory_id == "test_001"
        assert read_records[1].trajectory_id == "test_002"
        assert read_records[0].has_consequential_failure == HasConsequentialFailure.YES
        assert read_records[1].first_failure_mechanism == FirstFailureMechanism.NONE


class TestSchemaDefinitions:
    """Test schema definitions and human-readable text"""

    def test_failure_mechanism_definitions_exist(self):
        """Test that failure mechanism definitions are present"""
        assert "SELECTION" in FAILURE_MECHANISM_DEFINITIONS
        assert "EXECUTION" in FAILURE_MECHANISM_DEFINITIONS

    def test_selection_definition(self):
        """Test SELECTION definition content"""
        sel = FAILURE_MECHANISM_DEFINITIONS["SELECTION"]
        assert sel["internal"] == "SELECTION"
        assert "chinese" in sel
        assert "explanation" in sel
        assert sel["mnemonic"] == "想错了"

    def test_execution_definition(self):
        """Test EXECUTION definition content"""
        exe = FAILURE_MECHANISM_DEFINITIONS["EXECUTION"]
        assert exe["internal"] == "EXECUTION"
        assert "chinese" in exe
        assert "explanation" in exe
        assert exe["mnemonic"] == "想对了但没做成"


class TestTemporalConsistency:
    """Test temporal consistency rules"""

    def test_detection_after_failure(self):
        """Detection should be after or at failure step"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.YES,
            first_consequential_failure_step=3,
            first_failure_mechanism=FirstFailureMechanism.EXECUTION,
            failure_recognized=FailureRecognized.YES,
            detection_step=5
        )

        # This is valid - detection happens after failure
        is_valid, _ = record.validate()
        assert is_valid

    def test_recovery_after_detection(self):
        """Recovery start should be at or after detection"""
        record = AnnotationRecordV3(
            trajectory_id="test_001",
            annotator_id="A001",
            annotator_type=AnnotatorType.HUMAN,
            has_consequential_failure=HasConsequentialFailure.YES,
            first_consequential_failure_step=3,
            first_failure_mechanism=FirstFailureMechanism.EXECUTION,
            failure_recognized=FailureRecognized.YES,
            detection_step=5,
            recovery_attempted=RecoveryAttempted.YES,
            recovery_start_step=6,
            recovery_outcome=RecoveryOutcome.SUCCESS
        )

        is_valid, _ = record.validate()
        assert is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
