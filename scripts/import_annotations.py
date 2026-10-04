"""
Annotation Importer
Converts manually exported Claude/Codex/Gemini annotation JSON to unified schema.

Usage:
    python scripts/import_annotations.py --source claude --file batch_annotations/claude_batch001.jsonl
    python scripts/import_annotations.py --source gpt --file batch_annotations/gpt_batch001.jsonl
    python scripts/import_annotations.py --source gemini --file batch_annotations/gemini_batch001.jsonl
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation.schema import (
    AnnotationRecord, AnnotatorType, FailureType,
    AgentDetected, RecoveryStatus
)


# Valid values for validation
VALID_FAILURE_TYPES = {"SELECTION", "EXECUTION", "RECOGNITION", "RECOVERY", "UNCERTAIN"}
VALID_AGENT_DETECTED = {"YES", "NO", "UNCLEAR"}
VALID_RECOVERY_STATUS = {"SUCCESS", "FAILED", "NONE", "UNKNOWN"}


class AnnotationImportError(Exception):
    """Raised when annotation import fails"""
    pass


def validate_annotation(data: dict) -> tuple[bool, list[str]]:
    """Validate an annotation record"""
    errors = []

    # Required fields
    required_fields = ["trajectory_id", "failure_type"]
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    # Failure type validation
    if "failure_type" in data:
        if data["failure_type"] not in VALID_FAILURE_TYPES:
            errors.append(f"Invalid failure_type: {data['failure_type']}")

    # Confidence range
    if "confidence" in data:
        conf = data["confidence"]
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            errors.append(f"Invalid confidence: {conf} (must be 0.0-1.0)")

    # Agent detected validation
    if "agent_detected_failure" in data:
        if data["agent_detected_failure"] not in VALID_AGENT_DETECTED:
            errors.append(f"Invalid agent_detected_failure: {data['agent_detected_failure']}")

    # Recovery status validation
    if "recovery_status" in data:
        if data["recovery_status"] not in VALID_RECOVERY_STATUS:
            errors.append(f"Invalid recovery_status: {data['recovery_status']}")

    return len(errors) == 0, errors


def normalize_annotation(data: dict, source: str, annotator_id: str, model: str) -> dict:
    """
    Normalize an annotation record to the unified schema.

    Handles variations in field names and formats from different sources.
    Supports both v1 (flat) and v2 (nested causal_analysis/label) formats.
    """
    normalized = {}

    # Core identifiers
    normalized["trajectory_id"] = data.get("trajectory_id", data.get("id", "unknown"))
    normalized["annotator_id"] = annotator_id
    normalized["annotator_model"] = model or data.get("model", data.get("annotator_model", "unknown"))
    normalized["annotator_type"] = AnnotatorType.LLM.value

    # Timestamp
    normalized["timestamp"] = data.get("timestamp", datetime.now().isoformat())

    # Trajectory hash
    normalized["trajectory_hash"] = data.get("trajectory_hash", "")

    # Provenance
    normalized["annotation_source"] = f"imported_from_{source}"
    normalized["prompt_version"] = data.get("prompt_version", "v2")
    normalized["guideline_version"] = data.get("guideline_version", "v1")
    normalized["temperature"] = data.get("temperature")
    normalized["model_snapshot"] = data.get("model_snapshot", "")

    # Handle v2 nested format: causal_analysis.first_failure_step
    causal_analysis = data.get("causal_analysis", {})

    # Store additional causal fields if present
    causal_why_qualifies = causal_analysis.get("why_qualifies", "")
    causal_why_preceding = causal_analysis.get("why_preceding_not", "")
    label = data.get("label", {})

    # First consequential failure step (supports v1 and v2)
    normalized["first_consequential_failure_step"] = (
        causal_analysis.get("first_failure_step") or
        data.get("first_failure_step") or
        data.get("first_consequential_failure_step")
    )
    if normalized["first_consequential_failure_step"] is not None:
        normalized["first_consequential_failure_step"] = int(normalized["first_consequential_failure_step"])

    # Failure type - normalize variations (supports v1 and v2)
    ft = (
        label.get("type") or
        data.get("failure_type") or
        data.get("type") or
        "UNCERTAIN"
    )
    ft_map = {
        "selection": "SELECTION",
        "execution": "EXECUTION",
        "recognition": "RECOGNITION",
        "recovery": "RECOVERY",
        "uncertain": "UNCERTAIN",
        "selection_failure": "SELECTION",
        "execution_failure": "EXECUTION",
        "recognition_failure": "RECOGNITION",
        "recovery_failure": "RECOVERY",
        "none": "UNCERTAIN",
        "no_failure": "UNCERTAIN",
    }
    normalized["failure_type"] = ft_map.get(ft.lower(), ft.upper()) if isinstance(ft, str) else ft

    # Confidence (supports v1 and v2)
    normalized["confidence"] = float(
        label.get("confidence") or
        data.get("confidence") or
        0.5
    )

    # Agent awareness (supports v1 and v2)
    agent_awareness = data.get("agent_awareness", {})
    ad = (
        agent_awareness.get("detected") or
        data.get("agent_detected_failure") or
        "UNCLEAR"
    )
    ad_map = {
        "yes": "YES", "true": "YES", "detected": "YES",
        "no": "NO", "false": "NO", "not_detected": "NO",
        "unclear": "UNCLEAR", "unknown": "UNCLEAR"
    }
    normalized["agent_detected_failure"] = ad_map.get(ad.lower(), ad.upper()) if isinstance(ad, str) else ad

    normalized["detection_step"] = (
        agent_awareness.get("detection_step") or
        data.get("detection_step")
    )

    # Recovery status (v1 format only - v2 uses agent_awareness structure)
    rs = data.get("recovery_status", "UNKNOWN")
    if rs == "UNKNOWN" and agent_awareness:
        # Infer recovery from awareness
        detected = normalized["agent_detected_failure"]
        if detected == "YES":
            rs = "FAILED"  # Detected but didn't recover
        elif detected == "NO":
            rs = "NONE"
    rs_map = {
        "success": "SUCCESS", "recovered": "SUCCESS",
        "failed": "FAILED", "failure": "FAILED",
        "none": "NONE", "no_recovery": "NONE",
        "unknown": "UNKNOWN"
    }
    normalized["recovery_status"] = rs_map.get(rs.lower(), rs.upper()) if isinstance(rs, str) else rs

    # Evidence
    normalized["evidence_steps"] = data.get("evidence_steps", [])
    if isinstance(normalized["evidence_steps"], int):
        normalized["evidence_steps"] = [normalized["evidence_steps"]]

    # Prefer causal_analysis text if available
    causal_text = ""
    if causal_analysis:
        causal_parts = [
            causal_analysis.get("what_happened", ""),
            causal_analysis.get("why_consequential", ""),
            causal_analysis.get("why_this_step", ""),
            f"[ONSET JUSTIFICATION] {causal_why_qualifies}" if causal_why_qualifies else "",
            f"[PRECEDING EXCLUSION] {causal_why_preceding}" if causal_why_preceding else "",
        ]
        causal_text = ". ".join(filter(None, causal_parts))

    normalized["evidence_text"] = (
        causal_text or
        data.get("evidence_text") or
        data.get("reasoning", "") or
        label.get("reasoning", "")
    )
    normalized["annotator_notes"] = data.get("annotator_notes", "")

    return normalized


def import_file(input_file: Path, source: str, annotator_id: str, model: str,
                output_file: Optional[Path] = None) -> tuple[int, int, list]:
    """
    Import annotations from a JSON/JSONL file.

    Returns:
        (total, imported, errors)
    """
    if output_file is None:
        output_dir = Path(f"data/annotations/raw/{source}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{annotator_id}_annotations.jsonl"

    total = 0
    imported = 0
    errors = []

    # Read input file
    if input_file.suffix == ".jsonl":
        with open(input_file, 'r', encoding='utf-8') as f:
            records = [json.loads(line) for line in f if line.strip()]
    elif input_file.suffix == ".json":
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both single record and array
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # Check if it's a batch file
                if "trajectories" in data or "annotations" in data:
                    records = data.get("annotations", data.get("trajectories", []))
                else:
                    records = [data]
            else:
                records = []
    else:
        raise AnnotationImportError(f"Unsupported file format: {input_file.suffix}")

    total = len(records)

    # Process records
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, record in enumerate(records):
            try:
                # Normalize
                normalized = normalize_annotation(record, source, annotator_id, model)

                # Validate
                is_valid, validation_errors = validate_annotation(normalized)
                if not is_valid:
                    errors.append({
                        "trajectory_id": normalized.get("trajectory_id", f"record_{i}"),
                        "errors": validation_errors
                    })
                    continue

                # Convert to AnnotationRecord
                ann_record = AnnotationRecord.from_dict(normalized)

                # Write
                f.write(json.dumps(ann_record.to_dict(), ensure_ascii=False) + '\n')
                imported += 1

            except Exception as e:
                errors.append({
                    "trajectory_id": record.get("trajectory_id", f"record_{i}"),
                    "errors": [str(e)]
                })

    return total, imported, errors


def generate_import_report(total: int, imported: int, errors: list,
                          input_file: Path, output_file: Path):
    """Generate an import report"""
    report = f"""
============================================================
Annotation Import Report
============================================================

Input:    {input_file}
Output:   {output_file}

Total records:     {total}
Successfully imported: {imported}
Failed:            {len(errors)}

Success rate:      {imported/total*100:.1f}%

"""

    if errors:
        report += f"\nFailed records ({len(errors)}):\n"
        for err in errors[:10]:  # Show first 10
            report += f"  - {err['trajectory_id']}: {err['errors']}\n"
        if len(errors) > 10:
            report += f"  ... and {len(errors) - 10} more\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="Import annotations from external sources")
    parser.add_argument("--file", type=str, required=True,
                        help="Input file (JSON or JSONL)")
    parser.add_argument("--source", type=str, required=True,
                        choices=["claude", "gpt", "gemini", "human"],
                        help="Source of annotations")
    parser.add_argument("--annotator_id", type=str, required=True,
                        help="Annotator identifier (e.g., claude-3-5-sonnet, gpt-4o)")
    parser.add_argument("--model", type=str, default="",
                        help="Model version (optional)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file (optional)")

    args = parser.parse_args()

    input_file = Path(args.file)
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        return

    output_file = Path(args.output) if args.output else None

    print(f"Importing annotations from {input_file}...")
    total, imported, errors = import_file(
        input_file, args.source, args.annotator_id, args.model, output_file
    )

    # Determine output file
    if output_file is None:
        output_file = Path(f"data/annotations/raw/{args.source}/{args.annotator_id}_annotations.jsonl")

    report = generate_import_report(total, imported, errors, input_file, output_file)
    print(report)


if __name__ == "__main__":
    main()
