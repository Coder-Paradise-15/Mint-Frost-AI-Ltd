"""Generate a small, deterministic Frost-V1 instruction-tuning dataset."""

import argparse
import json
from pathlib import Path


SCENARIOS = [
    ("python", "A Python function is slow when processing a large list.", "Explain how to profile it and reduce unnecessary work."),
    ("python", "A dictionary lookup raises KeyError in production.", "Show a defensive fix and explain when each option is appropriate."),
    ("javascript", "A browser button works once and then stops responding.", "Debug the likely event-listener lifecycle issue."),
    ("javascript", "An API request sometimes returns invalid JSON.", "Design a resilient client-side error path."),
    ("git", "I committed a secret to a local Git repository.", "Describe how to remove it safely and rotate the secret."),
    ("git", "Two developers changed the same configuration file.", "Give a careful conflict-resolution workflow."),
    ("sql", "A query became slow after a table grew.", "Suggest an investigation using query plans and indexes."),
    ("sql", "A user can see another user's records.", "Identify the authorization boundary that must be enforced."),
    ("api", "A POST endpoint receives duplicate requests.", "Explain how to make the operation idempotent."),
    ("api", "A service returns HTTP 500 for malformed input.", "Recommend validation and appropriate status codes."),
    ("docker", "A container exits immediately after starting.", "Give a concise debugging checklist."),
    ("docker", "A Docker image is much larger than expected.", "Reduce its size without hiding runtime dependencies."),
    ("testing", "A test passes locally but fails in CI.", "Create a systematic diagnosis plan."),
    ("testing", "A flaky test depends on time and network state.", "Refactor it for deterministic behavior."),
    ("security", "A login endpoint is receiving many failed attempts.", "Prioritize practical protections and observability."),
    ("security", "A form accepts user-provided HTML.", "Explain safe output handling and the limits of sanitization."),
    ("architecture", "A monolith needs one background job queue.", "Compare a minimal first step with a larger redesign."),
    ("architecture", "A service needs to handle graceful shutdown.", "List the lifecycle steps for an HTTP worker."),
    ("emotional_support", "I am overwhelmed by a bug near a deadline.", "Help me turn the situation into the next three concrete actions."),
    ("emotional_support", "I solved a difficult production issue.", "Respond warmly and suggest a useful retrospective."),
]

STYLES = [
    ("curious", "The user sounds curious and wants to understand the reasoning."),
    ("urgent", "The user sounds rushed, so lead with the safest actionable step."),
    ("frustrated", "The user sounds frustrated, so acknowledge that without becoming vague."),
    ("focused", "The user is focused on a practical result and prefers concise structure."),
    ("encouraged", "The user would benefit from calm, confidence-building guidance."),
]


def make_record(index, scenario, style):
    category, question, instruction = scenario
    style_name, style_guidance = style
    user_text = f"{question} {instruction}"
    thought = (
        "<frost_thought>\n"
        f"[Emotional Stance]: The interaction is {style_name}; {style_guidance}\n"
        "[System Audit]: Role is USER. Treat the request as running on a 4-vCPU, 16GB RAM Codespace and avoid assuming unavailable services.\n"
        "[Synthesis Strategy]: Identify the controlling failure mode, provide ordered steps, and call out verification and security risks.\n"
        "</frost_thought>"
    )
    answer = (
        f"{thought}\n\n"
        f"Start with the smallest observable check for this {category} problem. "
        "Then apply the least invasive fix, verify it with a focused test, and document the remaining risk. "
        "Keep secrets out of logs and prefer reversible changes."
    )
    return {
        "id": f"frost-v1-{index:03d}",
        "category": category,
        "messages": [
            {"role": "system", "content": "You are Frost-V1, a precise and emotionally perceptive coding assistant."},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": answer},
        ],
    }


def generate_dataset(output_path, sample_count=100):
    if sample_count != len(SCENARIOS) * len(STYLES):
        raise ValueError("The built-in generator produces exactly 100 samples")
    records = [
        make_record(index, scenario, style)
        for index, (scenario, style) in enumerate(
            ((scenario, style) for scenario in SCENARIOS for style in STYLES), 1
        )
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as dataset_file:
        for record in records:
            dataset_file.write(json.dumps(record, ensure_ascii=True) + "\n")
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("frost_engine/frost_v1_dataset.jsonl"))
    parser.add_argument("--samples", type=int, default=100, help="Must remain 100 for this balanced dataset")
    args = parser.parse_args()
    count = generate_dataset(args.output, args.samples)
    print(f"Wrote {count} samples to {args.output}")


if __name__ == "__main__":
    main()
