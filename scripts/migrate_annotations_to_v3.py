"""
Migration Script: Schema v1 → v3

Converts existing annotation records from the old schema to Schema v3.

Usage:
    python scripts/migrate_annotations_to_v3.py
    python scripts/migrate_annotations_to_v3.py --input data/annotations/annotations.jsonl --output data/annotations/annotations_v3.jsonl

Note: Heuristic annotations are migrated but marked with annotator_type = HEURISTIC
      and will NOT be included in Human Gold.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema import (
    AnnotationRecord, AnnotatorType, FailureType, AgentDetected, RecoveryStatus
)
from src.annotation.schema_v3 import (
    AnnotationRecordV3, AnnotatorType as V3AnnotatorType,
    HasConsequentialFailure, FirstFailureMechanism,
    FailureRecognized, RecognitionFailure,
    RecoveryAttempted, RecoveryOutcome, ConfidenceLevel
)


def map_annotator_type(old_type: AnnotatorType) -> V3AnnotatorType:
    """Map v1 AnnotatorType to v3"""
    mapping = {
        AnnotatorType.HUMAN: V3AnnotatorType.HUMAN,
        AnnotatorType.LLM: V3AnnotatorType.LLM,
        AnnotatorType.HEURISTIC: V3AnnotatorType.HEURISTIC,
    }
    return mapping.get(old_type, V3AnnotatorType.HUMAN)


def map_failure_type_to_mechanism(old_failure_type: FailureType) -> FirstFailureMechanism:
    """
    Map old failure_type to new first_failure_mechanism.

    Important: RECOGNITION and RECOVERY are no longer onset mechanisms.
    They are analyzed as downstream variables.
    """
    if old_failure_type == FailureType.SELECTION:
        return FirstFailureMechanism.SELECTION
    elif old_failure_type == FailureType.EXECUTION:
        return FirstFailureMechanism.EXECUTION
    elif old_failure_type in [FailureType.RECOGNITION, FailureType.RECOVERY]:
        # These are downstream - assume SELECTION as the actual onset
        # (This is a heuristic; Human Gold will override this)
        return FirstFailureMechanism.UNCERTAIN
    else:
        return FirstFailureMechanism.NONE


def map_confidence(old_confidence) -> ConfidenceLevel:
    """Map old confidence (0.0-1.0 or string) to new ConfidenceLevel"""
    if isinstance(old_confidence, str):
        old_confidence = old_confidence.lower()
        if old_confidence == "high":
            return ConfidenceLevel.HIGH
        elif old_confidence == "medium":
            return ConfidenceLevel.MEDIUM
        elif old_confidence == "low":
            return ConfidenceLevel.LOW

    # Numeric confidence
    if isinstance(old_confidence, (int, float)):
        if old_confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif old_confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    return ConfidenceLevel.MEDIUM


def migrate_record(record: AnnotationRecord) -> AnnotationRecordV3:
    """
    Migrate a single v1 record to v3.

    This is a best-effort migration. Human Gold will override these labels.
    """
    # Determine has_consequential_failure
    if record.first_consequential_failure_step is None:
        has_failure = HasConsequentialFailure.NO
        mechanism = FirstFailureMechanism.NONE
        failure_step = None
    else:
        has_failure = HasConsequentialFailure.YES
        mechanism = map_failure_type_to_mechanism(record.failure_type)
        failure_step = record.first_consequential_failure_step

    # Map detection to recognition
    if record.agent_detected_failure == AgentDetected.YES:
        failure_recognized = FailureRecognized.YES
        detection_step = record.detection_step
    elif record.agent_detected_failure == AgentDetected.NO:
        failure_recognized = FailureRecognized.NO
        detection_step = None
    else:
        failure_recognized = FailureRecognized.UNCLEAR
        detection_step = None

    # Map recovery
    if record.recovery_status == RecoveryStatus.SUCCESS:
        recovery_attempted = RecoveryAttempted.YES
        recovery_outcome = RecoveryOutcome.SUCCESS
    elif record.recovery_status == RecoveryStatus.FAILED:
        recovery_attempted = RecoveryAttempted.YES
        recovery_outcome = RecoveryOutcome.FAILED
    elif record.recovery_status == RecoveryStatus.NONE:
        recovery_attempted = RecoveryAttempted.NOT_ATTEMPTED
        recovery_outcome = RecoveryOutcome.NOT_ATTEMPTED
    else:
        recovery_attempted = RecoveryAttempted.UNCLEAR
        recovery_outcome = RecoveryOutcome.UNCLEAR

    # Determine recognition_failure
    if has_failure == HasConsequentialFailure.YES:
        if failure_recognized == FailureRecognized.NO:
            recognition_failure = RecognitionFailure.YES
        elif failure_recognized == FailureRecognized.YES:
            recognition_failure = RecognitionFailure.NO
        else:
            recognition_failure = RecognitionFailure.UNCLEAR
    else:
        recognition_failure = RecognitionFailure.UNCLEAR

    # Evidence steps from old record
    evidence_steps = record.evidence_steps if record.evidence_steps else []
    if failure_step is not None and failure_step not in evidence_steps:
        evidence_steps = [failure_step] + evidence_steps

    # Causal analysis
    causal_analysis = {
        "onset": record.evidence_text if record.evidence_text else "",
        "recognition": "",
        "recovery": ""
    }

    return AnnotationRecordV3(
        trajectory_id=record.trajectory_id,
        annotator_id=record.annotator_id,
        annotator_type=map_annotator_type(record.annotator_type),

        task_type="",  # Old schema didn't have this
        task_success=None,  # Old schema didn't have this
        trajectory_hash=record.trajectory_hash,

        has_consequential_failure=has_failure,
        first_consequential_failure_step=failure_step,
        first_failure_mechanism=mechanism,

        failure_recognized=failure_recognized,
        detection_step=detection_step,
        recognition_failure=recognition_failure,

        recovery_attempted=recovery_attempted,
        recovery_start_step=None,  # Old schema didn't have this
        recovery_outcome=recovery_outcome,

        evidence_steps=evidence_steps,
        causal_analysis=causal_analysis,

        confidence=map_confidence(record.confidence),
        annotator_notes=record.annotator_notes,
        schema_version="v3",
        guideline_version="v1_to_v3_migration",
        created_at=record.timestamp,
        updated_at=datetime.now().isoformat()
    )


def migrate_file(input_path: str, output_path: str) -> dict:
    """Migrate annotations from a single file"""
    migrated = []
    errors = []

    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                old_record = AnnotationRecord.from_dict(json.loads(line))
                new_record = migrate_record(old_record)

                # Validate
                is_valid, errs = new_record.validate()
                if not is_valid:
                    errors.append(f"Line {line_num}: {', '.join(errs)}")

                migrated.append(new_record)
            except Exception as e:
                errors.append(f"Line {line_num}: {str(e)}")

    # Write output
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for record in migrated:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')

    return {
        "input": input_path,
        "output": output_path,
        "total": len(migrated),
        "errors": len(errors),
        "error_details": errors
    }


def main():
    parser = argparse.ArgumentParser(description="Migrate annotations from Schema v1 to v3")
    parser.add_argument("--input", type=str, default="data/annotations/annotations.jsonl",
                       help="Input file (v1 annotations)")
    parser.add_argument("--output", type=str, default="data/annotations/annotations_v3.jsonl",
                       help="Output file (v3 annotations)")
    parser.add_argument("--dir", type=str, default=None,
                       help="Migrate all .jsonl files in a directory")
    args = parser.parse_args()

    print("=" * 60)
    print("Schema Migration: v1 → v3")
    print("=" * 60)

    if args.dir:
        # Migrate all files in directory
        input_dir = Path(args.dir)
        results = []

        for jsonl_file in input_dir.glob("*.jsonl"):
            output_file = jsonl_file.parent / f"{jsonl_file.stem}_v3.jsonl"
            print(f"\nMigrating: {jsonl_file}")
            result = migrate_file(str(jsonl_file), str(output_file))
            results.append(result)
            print(f"  -> {output_file}: {result['total']} records, {result['errors']} errors")

        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        total_migrated = sum(r['total'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        print(f"Total files: {len(results)}")
        print(f"Total records migrated: {total_migrated}")
        print(f"Total errors: {total_errors}")

    else:
        # Migrate single file
        result = migrate_file(args.input, args.output)

        print(f"\nInput:  {result['input']}")
        print(f"Output: {result['output']}")
        print(f"Migrated: {result['total']} records")
        print(f"Errors: {result['errors']}")

        if result['errors'] > 0:
            print("\nError details:")
            for err in result['error_details'][:10]:
                print(f"  - {err}")
            if len(result['error_details']) > 10:
                print(f"  ... and {len(result['error_details']) - 10} more")


if __name__ == "__main__":
    main()
