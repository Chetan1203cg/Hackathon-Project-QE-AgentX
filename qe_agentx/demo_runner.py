"""
demo_runner.py
==============
Hackathon demo script — runs the full QE AgentX pipeline locally
using an existing story JSON file (no live Jira connection needed).

Usage:
    python demo_runner.py

Output:
    - Prints pipeline progress to console
    - Writes Markdown, JSON, and CSV to demo_output/
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from core.file_preservation import available_path
from exports.csv_exporter import CsvExporter
from exports.json_exporter import JsonExporter
from exports.markdown_exporter import MarkdownExporter
from orchestrator.graph import build_graph
from orchestrator.state import AgentXState

# ------------------------------------------------------------------ #
# Configuration — uses existing data file as demo input
# ------------------------------------------------------------------ #
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--story", default=None)
_args, _ = _parser.parse_known_args()

DEMO_STORY_PATH = (
    Path(_args.story).resolve() if _args.story
    else Path(__file__).parent.parent / "data" / "NGWD6-50396_story.json"
)
OUTPUT_DIR = Path(__file__).parent / "demo_output"

DEMO_HITL_RESPONSE = (
    "Please cover both feature toggle states: "
    "active (NBD'26 design visible) and inactive (legacy design visible)."
)

ACCESSIBILITY_HITL_RESPONSE = (
    "Use the approved site-wide focus treatment as the baseline and cover both "
    "Classic Search and AI Search across desktop, tablet, and mobile viewports."
)


def load_demo_story() -> dict:
    with open(DEMO_STORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_demo():
    print("\n" + "=" * 60)
    print("  QE AgentX — Hackathon Demo Runner")
    print("=" * 60)

    settings = Settings()
    
    # Show mode (Mock or Production)
    if settings.is_mock_mode:
        print("\n[MOCK MODE ENABLED]")
        print("   • No Azure OpenAI credentials detected")
        print("   • Using realistic mock responses for all agents")
        print("   • Demo results are deterministic and hardcoded")
    else:
        print("\n[PRODUCTION MODE]")
        print("   • Azure OpenAI credentials loaded")
        print("   • Using live GPT-4o for agent inference")
    
    story = load_demo_story()
    run_id = str(uuid.uuid4())[:8]
    hitl_response = (
        ACCESSIBILITY_HITL_RESPONSE
        if story["key"] == "NGWD6-52184"
        else DEMO_HITL_RESPONSE
    )

    print(f"\n[STORY] {story['key']} — {story['summary'][:60]}...")
    print(f"[RUN ID] {run_id}")

    initial_state: AgentXState = {
        "run_id": run_id,
        "story_id": story["key"],
        "raw_story": story,
        "release_version": "Version_VXXXX",
        "target_environment": "test",
        "structured_requirement": None,
        "behaviour_tree": None,
        "test_cases": [],
        "test_data": None,
        "coverage_map": None,
        "rtm": None,
        "review_report": None,
        "final_report": None,
        "deployment_report": None,
        "vector_validation_report": None,
        "health_check": None,
        "automation_execution": None,
        "schema_validation_report": None,
        "release_decision": None,
        "manual_qa": {"status": "PENDING_HUMAN_EXECUTION", "results": []},
        "ambiguities": [],
        "hitl_pending": False,
        "hitl_response": None,
        "errors": [],
        "current_stage": "Starting",
        "messages": [],
    }

    graph = build_graph(settings)
    config = {"configurable": {"thread_id": run_id}}

    # ------------------------------------------------------------------ #
    # Stream pipeline events
    # ------------------------------------------------------------------ #
    final_state = dict(initial_state)

    for chunk in graph.stream(initial_state, config=config):
        for node_name, output in chunk.items():
            if isinstance(output, dict):
                final_state.update(output)
                stage = output.get("current_stage", node_name)
                print(f"  [OK] {stage}")

                # Handle HITL interrupt automatically in demo mode
                if output.get("hitl_pending"):
                    ambiguities = output.get("ambiguities", [])
                    print(f"\n  [HITL GATE] {len(ambiguities)} clarification(s) needed:")
                    for q in ambiguities:
                        print(f"     → {q}")
                    print(f"\n  [AUTO-RESPONSE] {hitl_response[:60]}...\n")

                    # Inject response and resume
                    graph.update_state(
                        config,
                        {"hitl_response": hitl_response, "hitl_pending": False},
                    )
                    # Continue from the interrupt point
                    for resume_chunk in graph.stream(None, config=config):
                        for rn, ro in resume_chunk.items():
                            if isinstance(ro, dict):
                                final_state.update(ro)
                                rs = ro.get("current_stage", rn)
                                print(f"  [OK] {rs}")

    # ------------------------------------------------------------------ #
    # Export artefacts
    # ------------------------------------------------------------------ #
    OUTPUT_DIR.mkdir(exist_ok=True)
    story_id = story["key"]

    md_path = available_path(OUTPUT_DIR / f"{story_id}_testcases.md")
    json_path = available_path(OUTPUT_DIR / f"{story_id}_xray.json")
    csv_path = available_path(OUTPUT_DIR / f"{story_id}_rtm.csv")

    md_path.write_text(MarkdownExporter().export(final_state), encoding="utf-8")
    json_path.write_text(JsonExporter().export(final_state), encoding="utf-8")
    csv_path.write_text(CsvExporter().export(final_state), encoding="utf-8")

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    coverage = final_state.get("coverage_map") or {}
    review = final_state.get("review_report") or {}
    test_cases = final_state.get("test_cases") or []
    rtm = final_state.get("rtm") or {}
    final_report = final_state.get("final_report") or {}

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Test Cases Generated : {len(test_cases)}")
    print(f"  AC Coverage          : {coverage.get('overall_coverage_pct', 0):.1f}%")
    print(f"  Quality Score        : {review.get('quality_score', 0):.0f}/100")
    print(f"  RTM Rows             : {rtm.get('total_rows', 0)}")
    print(f"  Gaps Detected        : {len(review.get('gaps_detected', []))}")
    print(f"  Errors               : {len(final_state.get('errors', []))}")
    print()
    if final_report.get("executive_summary"):
        print("  Executive Summary:")
        print(f"  {final_report['executive_summary']}")
    print()
    print(f"  [MD] Markdown  → {md_path}")
    print(f"  [JSON] Xray JSON → {json_path}")
    print(f"  [CSV] RTM CSV   → {csv_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_demo()
