"""
Automatic Jira -> Test Cases -> Markdown pipeline.

Usage:
    python jira_to_testcases.py --jira-link <JIRA_ISSUE_URL>
    python jira_to_testcases.py NGWD6-12345

Output: output/<SPRINT>/<ISSUE_KEY>_testcases_functional.md (Markdown format)

Config:
    Expects config.json with these keys:
    {
      "jira": {
        "email": "you@company.com",
        "api_token": "ATATT..."
      }
    }
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

from generate_testcases import load_config


def extract_issue_key(jira_link: str) -> str:
    match = re.search(r"([A-Z][A-Z0-9]+-\d+)", jira_link)
    if not match:
        raise ValueError("Could not extract Jira issue key from URL")
    return match.group(1)


def extract_base_url(jira_link: str) -> str:
    match = re.match(r"(https?://[^/]+)", jira_link)
    if not match:
        raise ValueError("Could not extract Jira base URL from link")
    return match.group(1)


def safe_console_text(text: str) -> str:
    """Return text safe to print in non-UTF-8 Windows terminals."""
    try:
        encoding = (sys.stdout.encoding or "utf-8")
        return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    except Exception:
        return text


def sanitize_folder_name(name: str) -> str:
    """Make a Jira-derived label safe for use as a Windows folder name."""
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", (name or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")
    return cleaned or "No_Sprint"


def extract_sprint_name_from_agile_fields(agile_fields: dict) -> str:
    """Pick the most relevant sprint name from Jira Agile issue fields."""
    if not isinstance(agile_fields, dict):
        return ""

    sprint = agile_fields.get("sprint")
    if isinstance(sprint, dict) and sprint.get("name"):
        return str(sprint["name"]).strip()

    closed = agile_fields.get("closedSprints")
    if isinstance(closed, list):
        for item in reversed(closed):
            if isinstance(item, dict) and item.get("name"):
                return str(item["name"]).strip()

    return ""


def adf_to_text(node) -> str:
    """Convert Atlassian Document Format JSON into readable plain text."""
    if node is None:
        return ""

    if isinstance(node, list):
        parts = [adf_to_text(child) for child in node]
        return "".join(parts)

    if not isinstance(node, dict):
        return str(node)

    node_type = node.get("type", "")
    content = node.get("content", [])

    if node_type == "text":
        return node.get("text", "")
    if node_type == "hardBreak":
        return "\n"
    if node_type in {"paragraph", "doc", "blockquote", "listItem"}:
        return adf_to_text(content)
    if node_type == "bulletList":
        items = []
        for item in content:
            txt = adf_to_text(item).strip()
            if txt:
                items.append(f"- {txt}")
        return "\n".join(items) + ("\n" if items else "")
    if node_type == "orderedList":
        items = []
        for idx, item in enumerate(content, start=1):
            txt = adf_to_text(item).strip()
            if txt:
                items.append(f"{idx}. {txt}")
        return "\n".join(items) + ("\n" if items else "")
    if node_type in {"heading", "panel", "expand"}:
        return adf_to_text(content) + "\n"

    return adf_to_text(content)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_headline_like_ac(text: str) -> bool:
    """Heuristic: short or colon-ended main bullet often acts as a headline."""
    txt = normalize_text(text)
    if not txt:
        return False
    if txt.endswith(":"):
        return True
    words = txt.split()
    return len(words) <= 6


def _adf_text_no_list_prefix(node: Any) -> str:
    """Extract readable text from ADF node without adding bullet/number prefixes."""
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join(_adf_text_no_list_prefix(child) for child in node)
    if not isinstance(node, dict):
        return str(node)

    node_type = node.get("type", "")
    content = node.get("content", [])

    if node_type == "text":
        return node.get("text", "")
    if node_type == "hardBreak":
        return "\n"
    if node_type in {"paragraph", "heading", "blockquote", "panel", "expand", "doc", "listItem"}:
        return _adf_text_no_list_prefix(content)
    if node_type in {"bulletList", "orderedList"}:
        return "\n".join(normalize_text(_adf_text_no_list_prefix(item)) for item in content if normalize_text(_adf_text_no_list_prefix(item)))
    return _adf_text_no_list_prefix(content)


def _extract_list_item_main_and_subs(item_node: dict) -> Tuple[str, List[str]]:
    """Split a Jira listItem into main bullet text and nested sub-bullet texts."""
    main_parts: List[str] = []
    sub_items: List[str] = []

    for child in item_node.get("content", []):
        child_type = child.get("type", "")
        if child_type in {"bulletList", "orderedList"}:
            for sub_item in child.get("content", []):
                sub_main, sub_subs = _extract_list_item_main_and_subs(sub_item)
                if sub_main:
                    sub_items.append(sub_main)
                for nested in sub_subs:
                    if nested:
                        sub_items.append(nested)
        else:
            txt = normalize_text(_adf_text_no_list_prefix(child))
            if txt:
                main_parts.append(txt)

    main_text = normalize_text(" ".join(main_parts))
    deduped_subs: List[str] = []
    seen = set()
    for s in sub_items:
        clean = normalize_text(s)
        if clean and clean.lower() not in seen:
            seen.add(clean.lower())
            deduped_subs.append(clean)

    return main_text, deduped_subs


def extract_ac_groups_from_adf(description_adf: dict) -> List[Dict[str, Any]]:
    """
    Parse AC section directly from Jira ADF and preserve bullet hierarchy.

    Rules:
    - Filled bullet = main AC group
    - Nested bullets = additional details for that main AC
    - If main bullet looks like a headline, only nested bullets are treated as testable AC points
    """
    if not isinstance(description_adf, dict):
        return []

    top_blocks = description_adf.get("content", [])
    if not isinstance(top_blocks, list):
        return []

    start_re = re.compile(r"^(acceptance\s*criteria|acs?)\s*:?$", re.IGNORECASE)
    stop_re = re.compile(
        r"^(premises\s*/\s*dependencies|contact\s*/\s*partners|definition\s+of\s+ready|definition\s+of\s+done)\s*:?$",
        re.IGNORECASE,
    )

    in_ac_section = False
    groups: List[Dict[str, Any]] = []

    for block in top_blocks:
        block_type = block.get("type", "")
        block_text = normalize_text(_adf_text_no_list_prefix(block))

        if not in_ac_section:
            if block_type in {"paragraph", "heading"} and start_re.match(block_text):
                in_ac_section = True
                continue
            # Handle "Acceptance Criteria:" as a numbered list item (orderedList)
            if block_type in {"bulletList", "orderedList"}:
                for item in block.get("content", []):
                    item_text = normalize_text(_adf_text_no_list_prefix(item))
                    if start_re.match(item_text):
                        in_ac_section = True
                        break
            continue

        if block_type in {"paragraph", "heading"} and stop_re.match(block_text):
            break
        # Also stop on a numbered list item that matches the stop section
        if block_type in {"bulletList", "orderedList"}:
            first_item_text = ""
            if block.get("content"):
                first_item_text = normalize_text(_adf_text_no_list_prefix(block["content"][0]))
            if stop_re.match(first_item_text):
                break

        if block_type in {"bulletList", "orderedList"}:
            for item in block.get("content", []):
                main_text, sub_items = _extract_list_item_main_and_subs(item)
                if main_text or sub_items:
                    groups.append(
                        {
                            "main": main_text,
                            "sub_items": sub_items,
                            "main_is_headline": bool(main_text and sub_items and is_headline_like_ac(main_text)),
                        }
                    )
        elif block_type == "paragraph" and block_text:
            # ACs stored as plain paragraphs (not bullets) — treat each as its own AC group
            groups.append({"main": block_text, "sub_items": [], "main_is_headline": False})

    return groups


_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did shall should "
    "will would can could may might must it its that this these those which what when "
    "where who whom how not no nor of in on at to for with by from up about into "
    "through during before after above below and or but if so because as than too also "
    "very just already only each every all both few more most other some such then they "
    "their them there here made make makes within regarding provided available possible "
    "changes displayed configured integrated remains implemented functionality "
    "additional initial existing new current user users author authors adds item items "
    "individually".split()
)


def _shorten_title(text: str, max_words: int = 5) -> str:
    """Produce a short, precise headline from an AC statement.

    Strategy: extract significant content words, keeping their original order,
    and join the first few into a concise title.
    """
    t = text.strip().rstrip(".")

    # Normalise possessives ("shop's" → "shop") before tokenising.
    t = re.sub(r"'s?\b", "", t)

    # Pull key content words (skip stop-words), preserve order.  Deduplicate
    # including stem-like overlap (e.g. shop / shopping keep only the first).
    raw_words = re.findall(r"[A-Za-z][A-Za-z-]+", t)
    seen: set = set()
    content: List[str] = []
    for w in raw_words:
        low = w.lower()
        # Skip stop-words and words whose stem is already seen.
        if low in _STOP_WORDS:
            continue
        stem = low.rstrip("s")[:4]  # rough 4-char prefix stem
        if low in seen or stem in seen:
            continue
        seen.add(low)
        seen.add(stem)
        content.append(w)

    if len(content) < 2:
        # For very short extractions, keep what we have — a single keyword
        # is still a better title than raw sentence fragments.
        if not content:
            content = t.split()[:max_words]

    headline = " ".join(content[:max_words]).title()
    return headline if headline else "Validation"


def _ac_to_action_step(text: str) -> str:
    """Convert an AC statement into a concise user-action or verification step."""
    t = text.strip().rstrip(".")
    lower = t.lower()

    # If the AC already reads like a user action, keep it.
    if lower.startswith(("click ", "open ", "navigate ", "select ", "enter ",
                         "add ", "remove ", "drag ", "scroll ", "type ",
                         "log in", "log out", "search ", "submit ",
                         "toggle ", "enable ", "disable ", "check ",
                         "uncheck ", "upload ", "download ", "press ")):
        return t[0].upper() + t[1:] + "."

    # "When …" / "If …" conditions → perform the described action.
    # Supports ", " or " then " or ": " as separator between condition and expectation.
    cond_match = re.match(
        r"(?i)^(when|if)\s+(.+?)(?:,\s*|\s+then\s+|:\s+)(.+)$", t
    )
    if cond_match:
        action_part = cond_match.group(2).strip().rstrip(",")
        expected = cond_match.group(3).strip()
        return f"Perform: {action_part}. Then verify that {expected[0].lower()}{expected[1:]}."

    # Short "No <noun>" phrases → "Verify that no <noun> is displayed."
    no_match = re.match(r"(?i)^no\s+(.+)$", t)
    if no_match and len(t.split()) <= 5:
        return f"Verify that no {no_match.group(1).lower()} is displayed."

    # Declarative statement → turn into a verification step.
    # Strip leading articles / subjects that just restate the system name.
    return f"Verify that {t[0].lower()}{t[1:]}."


def build_steps_for_ac_group(main_text: str, sub_items: List[str], main_is_headline: bool) -> List[str]:
    """Build clear, action-oriented test steps from grouped AC bullets."""
    steps: List[str] = ["Navigate to the relevant page/feature in the test environment."]

    if main_text and not main_is_headline:
        steps.append(_ac_to_action_step(main_text))

    if sub_items:
        for sub in sub_items:
            steps.append(_ac_to_action_step(sub))

    return steps


def extract_acceptance_criteria(description: str) -> List[str]:
    """Extract acceptance criteria items from plain-text Jira description."""
    if not description:
        return []

    start_match = re.search(r"Acceptance\s*criteria\s*:?", description, flags=re.IGNORECASE)
    if not start_match:
        return []

    tail = description[start_match.end():]
    stop_markers = [
        "Figma link:",
        "Premises / Dependencies:",
        "Contact / Partners:",
        "Definition of Ready:",
        "Definition of Done:",
    ]
    stop_index = len(tail)
    for marker in stop_markers:
        idx = tail.find(marker)
        if idx != -1:
            stop_index = min(stop_index, idx)
    ac_text = tail[:stop_index].strip()

    # Split by bullets/newlines first, then sentence boundaries as fallback.
    lines = [ln.strip(" -\t\r\n") for ln in ac_text.splitlines() if ln.strip()]
    items: List[str] = []
    if len(lines) > 1:
        items = lines
    else:
        # Sentence-based split keeps concise AC points for Jira exports on one line.
        items = [s.strip() for s in re.split(r"\.\s+", ac_text) if s.strip()]

    cleaned = []
    for item in items:
        normalized = re.sub(r"\s+", " ", item).strip()
        if normalized and len(normalized) > 8:
            if not normalized.endswith("."):
                normalized += "."
            cleaned.append(normalized)

    return cleaned


def extract_ac_blocks(description: str) -> List[Tuple[str, str]]:
    """Extract structured AC blocks like (AC1): ... (AC2): ..."""
    if not description:
        return []

    start_match = re.search(r"Acceptance\s*criteria\s*:?", description, flags=re.IGNORECASE)
    if not start_match:
        return []

    tail = description[start_match.end():]
    stop_markers = [
        "Figma link:",
        "Premises / Dependencies:",
        "Contact / Partners:",
        "Definition of Ready:",
        "Definition of Done:",
    ]
    stop_index = len(tail)
    for marker in stop_markers:
        idx = tail.find(marker)
        if idx != -1:
            stop_index = min(stop_index, idx)
    ac_text = tail[:stop_index].strip()

    blocks = []
    # Detect labels even when text is poorly spaced, e.g. "...shadowAC3: ...".
    # Supports: (AC1):, AC1:, AC 1:, AV2: (AV is normalized to AC).
    label_pattern = re.compile(r"\(?\s*(A[CV]\s*\d+)\s*\)?\s*:", re.IGNORECASE)
    label_matches = list(label_pattern.finditer(ac_text))

    for idx, match in enumerate(label_matches):
        ac_id_raw = match.group(1) or ""
        ac_id = re.sub(r"\s+", "", ac_id_raw).upper().replace("AV", "AC", 1)
        body_start = match.end()
        body_end = label_matches[idx + 1].start() if idx + 1 < len(label_matches) else len(ac_text)
        body = ac_text[body_start:body_end].strip()
        body = re.sub(r"\s+", " ", body)
        if body:
            blocks.append((ac_id, body))

    return blocks


def extract_module_field_pairs(text: str) -> Dict[str, List[str]]:
    """Extract mappings like '- Focus Teaser Section: Link URL, Link Label'."""
    pairs: Dict[str, List[str]] = {}
    if not text:
        return pairs

    # Match bullet entries even when first bullet is inline after sentence text.
    pattern = re.compile(r"-\s*([^:\n]+):\s*(.*?)(?=\s+-\s*[^:\n]+:|\n|$)")
    for match in pattern.finditer(text):
        module = re.sub(r"\s+", " ", match.group(1)).strip()
        field_blob = re.sub(r"\s+", " ", match.group(2)).strip()
        split_fields = re.split(r"\s*\+\s*|\s*,\s*", field_blob)
        fields = [re.sub(r"\s+", " ", fld).strip(" .") for fld in split_fields if fld.strip()]
        if module and fields:
            pairs[module] = fields

    return pairs


def build_steps_for_ac(ac_id: str, ac_text: str, module_pairs: Dict[str, List[str]], feature_name: str = "") -> List[str]:
    """Create concrete test steps with module/field-specific actions."""
    steps: List[str] = [
        "Open AEM Content Fragment Editor.",
    ]
    component = feature_name if feature_name else "the relevant component"

    if module_pairs:
        for module, fields in module_pairs.items():
            if len(fields) >= 2:
                left = fields[0]
                right = fields[1]
                field_text = f"{left} and {right}"
            else:
                field_text = ", ".join(fields)

            steps.append(f"Open {module} content fragment.")
            if ac_id == "AC1":
                steps.append(
                    f"Verify a red asterisk (*) is displayed next to {field_text}."
                )
            elif ac_id == "AC2":
                steps.append(
                    f"Fill both {field_text} and verify no validation error is shown."
                )
                steps.append(
                    f"Clear both {field_text} and verify no validation error is shown."
                )
            elif ac_id == "AC3":
                steps.append(
                    f"Fill only {fields[0]} and leave {fields[1] if len(fields) > 1 else 'the linked field'} empty."
                )
                steps.append(
                    "Verify validation error appears on both linked fields and save is blocked."
                )
                steps.append(
                    "Reload the page and verify the previous persisted value is restored."
                )
                steps.append(
                    "Clear the remaining field and verify errors disappear and empty values are saved automatically."
                )
            elif ac_id == "AC4":
                steps.append(
                    f"Create invalid state for {field_text} by filling only one field."
                )
                steps.append(
                    f"Correct the state by either filling both fields or clearing both fields for {field_text}."
                )
                steps.append(
                    "Verify all error messages disappear immediately and blocked save completes automatically."
                )
            else:
                steps.append(
                    f"Execute validation check for linked fields {field_text} according to acceptance criteria."
                )
    else:
        steps = [
            "Navigate to the dealer frontend page in the test environment.",
            f"Locate the {component} section on the page.",
            f"Verify the visual/behavioral change described in {ac_id} against the Figma design.",
            "Compare the rendered result with the expected design (colors, spacing, corner radius, etc.).",
        ]

    return steps


def rule_based_test_data(story: dict) -> dict:
    """Generate deterministic test cases when no AI API is available."""
    description = story.get("description", "")
    description_adf = story.get("description_adf")
    ac_groups = extract_ac_groups_from_adf(description_adf)
    ac_blocks = extract_ac_blocks(description)
    ac_items = extract_acceptance_criteria(description)

    # Some Jira exports flatten AC paragraphs into a single line; when we have
    # structured AC blocks, prefer them for a clean AC list.
    if ac_blocks and len(ac_items) <= 1:
        ac_items = [f"{ac_id}: {ac_body}" for ac_id, ac_body in ac_blocks]

    if ac_groups:
        grouped_items: List[str] = []
        for group in ac_groups:
            main_text = normalize_text(group.get("main", ""))
            sub_items = [normalize_text(s) for s in group.get("sub_items", []) if normalize_text(s)]
            main_is_headline = bool(group.get("main_is_headline"))

            if sub_items and main_is_headline:
                grouped_items.extend(sub_items)
            elif sub_items and main_text:
                grouped_items.append(f"{main_text} Details: {'; '.join(sub_items)}")
            elif main_text:
                grouped_items.append(main_text)

        if grouped_items:
            ac_items = grouped_items

    if not ac_items and ac_blocks:
        ac_items = [body for _, body in ac_blocks]
    if not ac_items:
        ac_items = [
            "Default values are correctly preselected according to module context.",
            "Alternative path options are available and selectable.",
            "User-selected path is applied on submission.",
        ]

    feature = story.get("summary", "Jira Story Test Coverage").strip()
    feature = feature[:60]

    test_cases = []
    if ac_groups:
        for idx, group in enumerate(ac_groups, start=1):
            main_text = normalize_text(group.get("main", ""))
            sub_items = [normalize_text(s) for s in group.get("sub_items", []) if normalize_text(s)]
            main_is_headline = bool(group.get("main_is_headline"))

            if sub_items and main_is_headline:
                expected_result = "; ".join(sub_items)
            elif sub_items and main_text:
                expected_result = f"{main_text} Details: {'; '.join(sub_items)}"
            else:
                expected_result = main_text

            if not expected_result:
                continue

            title_suffix = _shorten_title(main_text) if main_text else f"AC Group {idx}"

            test_cases.append(
                {
                    "title": f"Test Case {idx} - {title_suffix}",
                    "description": f"Validate grouped acceptance criteria: {expected_result}",
                    "preconditions": [
                        "User is logged in with required permissions.",
                        "Affected feature/page/module is accessible in the target environment.",
                    ],
                    "steps": build_steps_for_ac_group(main_text, sub_items, main_is_headline),
                    "expected_result": expected_result,
                }
            )
    elif ac_blocks:
        for idx, (ac_id, ac_body) in enumerate(ac_blocks, start=1):
            module_pairs = extract_module_field_pairs(ac_body)
            steps = build_steps_for_ac(ac_id, ac_body, module_pairs, feature_name=story.get("summary", ""))

            test_cases.append(
                {
                    "title": f"Test Case {idx} - {ac_id} Validation",
                    "description": f"Validate {ac_id}: {ac_body}",
                    "preconditions": [
                        "User is logged in with required permissions.",
                        "The dealer frontend page is accessible in the test environment.",
                        "A Figma design reference is available for visual comparison.",
                    ],
                    "steps": steps,
                    "expected_result": ac_body,
                }
            )
    else:
        for idx, ac in enumerate(ac_items, start=1):
            test_cases.append(
                {
                    "title": f"Test Case {idx} - {_shorten_title(ac)}",
                    "description": f"Validate acceptance criterion: {ac}",
                    "preconditions": [
                        "User is logged in with required permissions.",
                        "Affected feature/page/module is accessible in the target environment.",
                    ],
                    "steps": [
                        "Navigate to the relevant page/feature in the test environment.",
                        _ac_to_action_step(ac),
                    ],
                    "expected_result": ac,
                }
            )

    return {
        "feature": feature,
        "test_scenario": "Validate path defaulting, alternative selection, and submit behavior.",
        "scenario_description": "Covers acceptance criteria from Jira story using deterministic test design.",
        "acceptance_criteria": ac_items,
        "test_cases": test_cases,
    }


def build_markdown(story: dict, test_data: dict) -> str:
    """Render test case data as a Markdown document matching the functional template."""
    key = story.get("key", "")
    summary = story.get("summary", "")
    link = story.get("link", "")

    lines: List[str] = []
    lines.append(f"# Test Cases - {summary}")
    lines.append("")
    lines.append(f"**User Story:** {key} {summary}  ")
    lines.append(f"**URL:** {link}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    scenario = test_data.get("test_scenario", "")
    if scenario:
        lines.append("## Test Scenario")
        lines.append("")
        lines.append(scenario)
        lines.append("")

    ac_list = test_data.get("acceptance_criteria", [])
    if ac_list:
        lines.append("## Acceptance Criteria")
        lines.append("")
        for ac in ac_list:
            lines.append(f"- {ac}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Test Cases")
    lines.append("")

    for tc in test_data.get("test_cases", []):
        title = tc.get("title", "")
        description = tc.get("description", "")
        preconditions = tc.get("preconditions", [])
        steps = tc.get("steps", [])
        expected = tc.get("expected_result", "")

        lines.append(f"### {title}")
        lines.append("")
        if description:
            lines.append(f"**Description:** {description}")
            lines.append("")
        if preconditions:
            lines.append("**Preconditions:**")
            for p in preconditions:
                lines.append(f"- {p}")
            lines.append("")
        if steps:
            lines.append("**Test Steps:**")
            for i, step in enumerate(steps, start=1):
                lines.append(f"{i}. {step}")
            lines.append("")
        if expected:
            lines.append(f"**Expected Result:**  ")
            lines.append(expected)
            lines.append("")
        lines.append("**Test Results:**")
        lines.append("- [ ] Pass")
        lines.append("- [ ] Fail")
        lines.append("- [ ] Blocked")
        lines.append("- Result notes: ")
        lines.append("- Defect/Jira link (if failed): ")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Screenshots / Evidence")
    lines.append("")
    lines.append("Document all screenshots, attachments, and evidence here:")
    lines.append("")
    lines.append("- [Add screenshot/evidence link here]")
    lines.append("")

    return "\n".join(lines)


def fetch_jira_story(jira_link: str, config: dict) -> dict:
    jira_cfg = config.get("jira", {})
    email = jira_cfg.get("email")
    api_token = jira_cfg.get("api_token")
    if not email or not api_token:
        raise ValueError(
            "Missing Jira credentials. Set JIRA_API_TOKEN as a user environment variable "
            "or add jira.api_token to config.json (not recommended)."
        )

    issue_key = extract_issue_key(jira_link)
    base_url = extract_base_url(jira_link)

    url = f"{base_url}/rest/api/3/issue/{issue_key}"
    params = {
        "fields": "summary,description,priority,status,components,assignee,issuetype"
    }

    response = requests.get(url, params=params, auth=(email, api_token), timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"Jira API request failed ({response.status_code}): {response.text[:300]}"
        )

    data = response.json()
    fields = data.get("fields", {})

    sprint_name = ""
    agile_url = f"{base_url}/rest/agile/1.0/issue/{issue_key}"
    try:
        agile_response = requests.get(agile_url, auth=(email, api_token), timeout=30)
        if agile_response.status_code == 200:
            agile_fields = agile_response.json().get("fields", {})
            sprint_name = extract_sprint_name_from_agile_fields(agile_fields)
    except Exception:
        sprint_name = ""

    description_adf = fields.get("description")
    description_text = adf_to_text(description_adf).strip()

    components = fields.get("components") or []
    component = components[0].get("name", "") if components else ""

    return {
        "key": data.get("key", issue_key),
        "summary": fields.get("summary", ""),
        "link": jira_link,
        "sprint": sprint_name,
        "type": (fields.get("issuetype") or {}).get("name", ""),
        "priority": (fields.get("priority") or {}).get("name", ""),
        "status": (fields.get("status") or {}).get("name", ""),
        "component": component,
        "assignee": (fields.get("assignee") or {}).get("displayName", ""),
        "description": description_text,
        "description_adf": description_adf,
    }


_JIRA_KEY_RE = re.compile(r'^[A-Z][A-Z0-9]+-\d+$')
_JIRA_BASE_URL = "https://vwgroup-b2b.atlassian.net"


def main():
    # Support bare issue key as first positional argument, e.g.: jira_to_testcases.py NGWD6-50342
    import sys as _sys
    _args_raw = _sys.argv[1:]
    if _args_raw and _JIRA_KEY_RE.match(_args_raw[0]):
        _sys.argv[1:] = ["--jira-link", f"{_JIRA_BASE_URL}/browse/{_args_raw[0]}"] + _args_raw[1:]

    parser = argparse.ArgumentParser(
        description="Automatically create test-case Markdown document from Jira link or issue key."
    )
    parser.add_argument("--jira-link", required=True, help="Full Jira issue link or bare issue key")
    parser.add_argument(
        "--config",
        "-c",
        default=str(Path(__file__).parent / "config.json"),
        help="Path to config.json",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output .md path (default: output/<ISSUE_KEY>_testcases_functional.md)",
    )
    parser.add_argument(
        "--dump-story",
        help="Optional path to write parsed Jira story JSON for debugging",
    )
    args = parser.parse_args()

    if not Path(args.config).exists():
        print(f"ERROR: Config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    config = load_config(args.config)

    print("Fetching Jira issue...")
    story = fetch_jira_story(args.jira_link, config)
    print(safe_console_text(f"  Issue: {story['key']} - {story['summary']}"))

    if args.dump_story:
        dump_path = Path(args.dump_story)
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        dump_path.write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Story dump: {dump_path}")

    print("Generating test cases...")
    test_data = rule_based_test_data(story)
    print("  Used rule-based generation")

    print(f"  Generated {len(test_data.get('test_cases', []))} test cases")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        sprint_label = sanitize_folder_name(story.get("sprint") or "No Sprint")
        sprint_dir = output_dir / sprint_label
        sprint_dir.mkdir(parents=True, exist_ok=True)
        output_path = sprint_dir / f"{story['key']}_testcases_functional.md"

    md_content = build_markdown(story, test_data)
    output_path.write_text(md_content, encoding="utf-8")
    print(f"Markdown saved: {output_path}")


if __name__ == "__main__":
    main()
