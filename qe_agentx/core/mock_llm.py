"""
core/mock_llm.py
=================
Mock LLM provider that returns realistic, deterministic outputs.
Used when Azure OpenAI credentials are unavailable (Demo Mode).
Outputs are based on the actual business problem and real Jira data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


class MockLLM:
    """
    Mock implementation of Azure OpenAI responses.
    All responses are realistic and grounded in the NGWD6-50396 CMS story.
    """

    def __init__(self):
        self.call_count = 0

    def invoke(self, payload: dict) -> dict:
        """
        Route to appropriate mock response based on payload content.
        In production, this is replaced by actual LLM inference.
        """
        self.call_count += 1

        # Detect which agent is calling by inspecting payload keys
        human_msg = str(payload.get("human_template", "")) + str(payload.get("text", ""))

        if "acceptance_criteria" in human_msg.lower() and "requirement" in human_msg.lower():
            return self._mock_requirement_agent(payload)
        elif "scenario" in human_msg.lower() or "behaviour tree" in human_msg.lower():
            return self._mock_scenario_agent(payload)
        elif "test case" in human_msg.lower():
            return self._mock_testcase_agent(payload)
        elif "test data" in human_msg.lower():
            return self._mock_testdata_agent(payload)
        elif "quality" in human_msg.lower() and "review" in human_msg.lower():
            return self._mock_review_agent(payload)
        elif "executive" in human_msg.lower() or "summary" in human_msg.lower():
            return self._mock_reporting_agent(payload)
        else:
            # Default: return empty structure
            return {}

    # ------------------------------------------------------------------ #
    # Agent-specific mock responses
    # ------------------------------------------------------------------ #

    def _mock_requirement_agent(self, _payload: dict) -> dict:
        """Mock output for Requirement Agent (Agent 1)."""
        if _payload.get("story_id") == "NGWD6-52184":
            return self._mock_52184_requirement()
        return {
            "story_id": "NGWD6-50396",
            "summary": "🔵 [CMS][NBD'26] S127 Feature Cluster Section (Simple) - Update as per new design",
            "component": "CMS",
            "priority": "Major",
            "sprint": "CMS Sprint 273",
            "acceptance_criteria": [
                {
                    "id": "AC-01",
                    "text": "Named items, section match the NBD'26 specifications from FIGMA",
                    "is_ambiguous": False,
                    "ambiguity_note": None,
                    "implicit_assumption": "FIGMA design mockups are available to the tester for visual comparison",
                },
                {
                    "id": "AC-02",
                    "text": "NBD changes are hidden behind the feature activation toggle on market level",
                    "is_ambiguous": True,
                    "ambiguity_note": "Behaviour when toggle is inactive is not explicitly defined",
                    "implicit_assumption": "Toggle controls visibility; legacy design should be reverted when inactive",
                },
                {
                    "id": "AC-03",
                    "text": "Storybook documentation updated with new component specs",
                    "is_ambiguous": False,
                    "ambiguity_note": None,
                    "implicit_assumption": "Storybook is the source of truth for component documentation",
                },
                {
                    "id": "AC-04",
                    "text": "SysDoc (System Documentation) updated to reflect NBD'26 changes",
                    "is_ambiguous": False,
                    "ambiguity_note": None,
                    "implicit_assumption": "SysDoc is maintained in Confluence or Wiki",
                },
            ],
            "nfr_hints": [
                "Performance: Component should render in < 200ms on tablet view",
                "Accessibility: WCAG 2.1 Level AA compliance required",
                "Responsive Design: 960px tablet view + 1280px+ desktop view",
                "Feature Toggle: RTL (Right-to-Left) language support via environment variable",
            ],
            "domain_keywords": ["CMS", "NBD'26", "FIGMA", "Feature Toggle", "Storybook", "Tablet View", "Responsive Design"],
            "clarifying_questions": [
                "Should tests cover both feature toggle states (active and inactive)?",
                "Is visual regression testing (FIGMA mockup comparison) in scope, or only functional?",
                "Should we test all market localizations or just en-US?",
            ],
            "overall_risk": "MEDIUM",
            "confidence_score": 0.92,
        }

    def _mock_scenario_agent(self, _payload: dict) -> dict:
        """Mock output for Scenario Agent (Agent 2)."""
        if _payload.get("story_id") == "NGWD6-52184":
            return self._mock_52184_scenarios()
        return {
            "story_id": "NGWD6-50396",
            "total_nodes": 11,
            "happy_path_count": 3,
            "alternate_flow_count": 3,
            "boundary_count": 3,
            "negative_count": 2,
            "nfr_count": 0,
            "root_nodes": [
                {
                    "node_id": "SN-001",
                    "ac_ref": "AC-01",
                    "flow_type": "happy_path",
                    "title": "S127 Feature Cluster displays with NBD'26 design when active",
                    "description": "Verify that Feature Cluster Section renders with the new NBD'26 FIGMA design when feature toggle is enabled",
                    "precondition": "Feature toggle for NBD'26 is enabled on test market",
                    "trigger_condition": "User navigates to page containing Feature Cluster",
                    "expected_state": "Feature Cluster displays new design with correct styling, layout, and named items",
                    "risk_level": "HIGH",
                    "children": [],
                },
                {
                    "node_id": "SN-002",
                    "ac_ref": "AC-01",
                    "flow_type": "boundary",
                    "title": "Feature Cluster responsive layout at 960px tablet viewport",
                    "description": "Verify layout adapts correctly at tablet breakpoint per NBD'26 specs",
                    "precondition": "Feature toggle enabled; viewport set to 960px width",
                    "trigger_condition": "Browser resized to tablet width",
                    "expected_state": "Boxes align right; no horizontal overflow; font sizes scale proportionally",
                    "risk_level": "MEDIUM",
                    "children": [],
                },
                {
                    "node_id": "SN-003",
                    "ac_ref": "AC-02",
                    "flow_type": "happy_path",
                    "title": "Feature toggle ACTIVE — NBD'26 design visible",
                    "description": "When feature toggle is ON, NBD'26 design elements are rendered",
                    "precondition": "Feature toggle = ON for market",
                    "trigger_condition": "Page load",
                    "expected_state": "New design elements visible; old design hidden",
                    "risk_level": "HIGH",
                    "children": [],
                },
                {
                    "node_id": "SN-004",
                    "ac_ref": "AC-02",
                    "flow_type": "happy_path",
                    "title": "Feature toggle INACTIVE — legacy design fallback",
                    "description": "When feature toggle is OFF, legacy design is displayed",
                    "precondition": "Feature toggle = OFF for market",
                    "trigger_condition": "Page load",
                    "expected_state": "Legacy design rendered; no new NBD'26 elements visible",
                    "risk_level": "HIGH",
                    "children": [],
                },
                {
                    "node_id": "SN-005",
                    "ac_ref": "AC-02",
                    "flow_type": "negative",
                    "title": "Toggle switch at runtime (no page reload) — design updates dynamically",
                    "description": "Toggling feature flag mid-session should update UI without page reload",
                    "precondition": "Toggle initially OFF; feature flag API available",
                    "trigger_condition": "Feature flag toggled to ON via admin API",
                    "expected_state": "Design updates in real-time; no page refresh required; no console errors",
                    "risk_level": "MEDIUM",
                    "children": [],
                },
                {
                    "node_id": "SN-006",
                    "ac_ref": "AC-03",
                    "flow_type": "happy_path",
                    "title": "Storybook components updated with NBD'26 specs",
                    "description": "Verify Storybook documentation reflects new component design",
                    "precondition": "Storybook deployed; Feature Cluster component registered",
                    "trigger_condition": "View Feature Cluster story in Storybook",
                    "expected_state": "Storybook displays new variant(s); props documented; use cases shown",
                    "risk_level": "LOW",
                    "children": [],
                },
                {
                    "node_id": "SN-007",
                    "ac_ref": "AC-04",
                    "flow_type": "happy_path",
                    "title": "SysDoc updated with component architecture",
                    "description": "System documentation contains updated Feature Cluster specs",
                    "precondition": "SysDoc accessible; update published",
                    "trigger_condition": "Access SysDoc Feature Cluster page",
                    "expected_state": "Page reflects NBD'26 design; links to FIGMA; version history visible",
                    "risk_level": "LOW",
                    "children": [],
                },
            ],
        }

    def _mock_testcase_agent(self, _payload: dict) -> dict:
        """Mock output for Test Case Agent (Agent 3)."""
        if _payload.get("story_id") == "NGWD6-52184":
            return self._mock_52184_test_cases()
        return {
            "story_id": "NGWD6-50396",
            "total": 12,
            "high_risk_count": 4,
            "medium_risk_count": 6,
            "low_risk_count": 2,
            "test_cases": [
                {
                    "tc_id": "TC-001",
                    "scenario_node_ref": "SN-001",
                    "ac_ref": "AC-01",
                    "title": "TC-001 – Feature Cluster displays NBD'26 design when active",
                    "description": "Verify that the Feature Cluster Section component renders with the new NBD'26 FIGMA design specifications",
                    "preconditions": [
                        "Feature toggle for NBD'26 is enabled for the test market",
                        "User has navigated to a page containing the Feature Cluster component",
                    ],
                    "steps": [
                        {
                            "step_number": 1,
                            "action": "Open the CMS page containing the Feature Cluster Section component",
                            "expected_result": None,
                        },
                        {
                            "step_number": 2,
                            "action": "Verify that the component title matches the NBD'26 FIGMA spec",
                            "expected_result": "Title styling, font size, and colour match the FIGMA mockup exactly",
                        },
                        {
                            "step_number": 3,
                            "action": "Verify each named item in the cluster displays with correct styling",
                            "expected_result": "All items have correct padding, borders, background colour per FIGMA spec",
                        },
                        {
                            "step_number": 4,
                            "action": "Verify layout alignment and spacing between items",
                            "expected_result": "Gaps and alignment match FIGMA; no overlaps; responsive padding applied",
                        },
                    ],
                    "expected_result": "Feature Cluster Section displays exactly as specified in NBD'26 FIGMA design; all named items visible and properly styled",
                    "risk_level": "HIGH",
                    "tags": ["regression", "smoke", "happy_path", "visual"],
                    "status": "DRAFT",
                    "gherkin": "Given the Feature Cluster component is rendered on a CMS page\nAnd the NBD'26 feature toggle is ENABLED\nWhen the page loads\nThen the component displays with NBD'26 design specifications\nAnd all named items are visible and properly styled",
                },
                {
                    "tc_id": "TC-002",
                    "scenario_node_ref": "SN-002",
                    "ac_ref": "AC-01",
                    "title": "TC-002 – Feature Cluster responsive at 960px tablet viewport",
                    "description": "Verify responsive layout at tablet breakpoint (960px)",
                    "preconditions": ["Feature toggle ENABLED", "Browser viewport at 960px width"],
                    "steps": [
                        {"step_number": 1, "action": "Set browser viewport to 960px width", "expected_result": None},
                        {
                            "step_number": 2,
                            "action": "Navigate to page with Feature Cluster",
                            "expected_result": "Component layout adapts; no horizontal scroll",
                        },
                        {
                            "step_number": 3,
                            "action": "Verify that 'All Features' box moves to right side of layout",
                            "expected_result": "Box is positioned right; space is optimised per NBD'26 tablet spec",
                        },
                        {
                            "step_number": 4,
                            "action": "Verify font sizes and padding scale appropriately",
                            "expected_result": "Text is readable; spacing is proportional; no clipping occurs",
                        },
                    ],
                    "expected_result": "Layout is responsive and matches NBD'26 tablet design specification at 960px",
                    "risk_level": "MEDIUM",
                    "tags": ["regression", "responsive", "boundary"],
                    "status": "DRAFT",
                    "gherkin": "Given viewport is 960px wide\nWhen Feature Cluster loads\nThen layout adapts for tablet\nAnd All Features box aligns right\nAnd text remains readable",
                },
                {
                    "tc_id": "TC-003",
                    "scenario_node_ref": "SN-003",
                    "ac_ref": "AC-02",
                    "title": "TC-003 – Toggle ON: NBD'26 design visible",
                    "description": "Verify that enabling the feature toggle shows the NBD'26 design",
                    "preconditions": ["Feature toggle is currently ENABLED for test market"],
                    "steps": [
                        {"step_number": 1, "action": "Verify feature toggle status is ON", "expected_result": None},
                        {"step_number": 2, "action": "Load page with Feature Cluster", "expected_result": None},
                        {
                            "step_number": 3,
                            "action": "Verify NBD'26 design elements are rendered (new styles, layout, colors)",
                            "expected_result": "New design is visible; legacy styles are not applied",
                        },
                    ],
                    "expected_result": "When toggle is ON, Feature Cluster displays the new NBD'26 design without legacy fallback",
                    "risk_level": "HIGH",
                    "tags": ["feature_toggle", "smoke"],
                    "status": "DRAFT",
                    "gherkin": "Given feature toggle is ON\nWhen page renders\nThen NBD'26 design is displayed",
                },
                {
                    "tc_id": "TC-004",
                    "scenario_node_ref": "SN-004",
                    "ac_ref": "AC-02",
                    "title": "TC-004 – Toggle OFF: legacy design fallback",
                    "description": "Verify that disabling the feature toggle shows the legacy design",
                    "preconditions": ["Feature toggle is currently DISABLED for test market"],
                    "steps": [
                        {"step_number": 1, "action": "Verify feature toggle status is OFF", "expected_result": None},
                        {"step_number": 2, "action": "Load page with Feature Cluster", "expected_result": None},
                        {
                            "step_number": 3,
                            "action": "Verify legacy design is rendered (old styles, layout, colors)",
                            "expected_result": "Legacy design is visible; no new NBD'26 elements appear",
                        },
                    ],
                    "expected_result": "When toggle is OFF, Feature Cluster displays the legacy design",
                    "risk_level": "HIGH",
                    "tags": ["feature_toggle", "smoke"],
                    "status": "DRAFT",
                    "gherkin": "Given feature toggle is OFF\nWhen page renders\nThen legacy design is displayed",
                },
                {
                    "tc_id": "TC-005",
                    "scenario_node_ref": "SN-005",
                    "ac_ref": "AC-02",
                    "title": "TC-005 – Toggle runtime switch updates design dynamically",
                    "description": "Verify design updates when toggle is switched during an active session (no reload)",
                    "preconditions": ["Page with Feature Cluster already loaded", "Toggle initially OFF"],
                    "steps": [
                        {"step_number": 1, "action": "Open Feature Cluster page with toggle OFF", "expected_result": "Legacy design visible"},
                        {
                            "step_number": 2,
                            "action": "Call feature flag API to toggle ON (mid-session)",
                            "expected_result": None,
                        },
                        {
                            "step_number": 3,
                            "action": "Verify Feature Cluster updates to NBD'26 design without page reload",
                            "expected_result": "Design updates in real-time; smooth transition; no page flicker",
                        },
                        {
                            "step_number": 4,
                            "action": "Check browser console for errors",
                            "expected_result": "No JavaScript errors; no CSS conflicts logged",
                        },
                    ],
                    "expected_result": "Runtime toggle switch updates the design dynamically without requiring a page reload",
                    "risk_level": "MEDIUM",
                    "tags": ["feature_toggle", "negative"],
                    "status": "DRAFT",
                    "gherkin": "Given Feature Cluster loaded with toggle OFF\nWhen feature flag is toggled to ON via API\nThen design updates immediately\nAnd no page reload occurs\nAnd no console errors appear",
                },
                {
                    "tc_id": "TC-006",
                    "scenario_node_ref": "SN-006",
                    "ac_ref": "AC-03",
                    "title": "TC-006 – Storybook documents Feature Cluster NBD'26 variant",
                    "description": "Verify Storybook contains updated Feature Cluster component documentation",
                    "preconditions": ["Storybook application is deployed and accessible"],
                    "steps": [
                        {"step_number": 1, "action": "Open Storybook and navigate to Feature Cluster story", "expected_result": None},
                        {
                            "step_number": 2,
                            "action": "Verify NBD'26 variant exists in the component stories",
                            "expected_result": "Variant is listed and renders correctly",
                        },
                        {
                            "step_number": 3,
                            "action": "Verify component props are documented",
                            "expected_result": "Props table shows all inputs with descriptions and types",
                        },
                        {
                            "step_number": 4,
                            "action": "Verify use case examples are provided",
                            "expected_result": "Multiple variants and usage examples are displayed",
                        },
                    ],
                    "expected_result": "Storybook contains complete documentation for NBD'26 Feature Cluster variant",
                    "risk_level": "LOW",
                    "tags": ["documentation"],
                    "status": "DRAFT",
                },
                {
                    "tc_id": "TC-007",
                    "scenario_node_ref": "SN-007",
                    "ac_ref": "AC-04",
                    "title": "TC-007 – SysDoc updated with Feature Cluster specs",
                    "description": "Verify System Documentation reflects NBD'26 Feature Cluster changes",
                    "preconditions": ["SysDoc system is accessible"],
                    "steps": [
                        {"step_number": 1, "action": "Navigate to Feature Cluster section in SysDoc", "expected_result": None},
                        {
                            "step_number": 2,
                            "action": "Verify updated component specifications are documented",
                            "expected_result": "New design specs, props, and behaviours are described",
                        },
                        {
                            "step_number": 3,
                            "action": "Verify links to FIGMA mockups are included",
                            "expected_result": "FIGMA design reference links are present and valid",
                        },
                        {
                            "step_number": 4,
                            "action": "Verify version history shows recent update",
                            "expected_result": "Update timestamp and author are recorded",
                        },
                    ],
                    "expected_result": "SysDoc is updated with complete NBD'26 Feature Cluster specifications",
                    "risk_level": "LOW",
                    "tags": ["documentation"],
                    "status": "DRAFT",
                },
            ],
        }

    def _mock_testdata_agent(self, _payload: dict) -> dict:
        """Mock output for Test Data Agent (Agent 4)."""
        if _payload.get("story_id") == "NGWD6-52184":
            return self._mock_52184_test_data()
        return {
            "story_id": "NGWD6-50396",
            "datasets": [
                {
                    "dataset_id": "DS-001",
                    "tc_ref": "TC-001",
                    "category": "valid",
                    "description": "Valid Feature Cluster with all named items populated",
                    "data": {
                        "component_title": "Feature Cluster",
                        "feature_toggle_state": "ENABLED",
                        "named_items": ["Item 1", "Item 2", "Item 3", "Item 4"],
                        "market": "en-US",
                    },
                    "notes": None,
                    "requires_provisioning": False,
                },
                {
                    "dataset_id": "DS-002",
                    "tc_ref": "TC-002",
                    "category": "boundary",
                    "description": "Viewport at exact 960px tablet breakpoint",
                    "data": {
                        "viewport_width": 960,
                        "viewport_height": 1024,
                        "device_type": "tablet",
                        "orientation": "portrait",
                    },
                    "notes": None,
                    "requires_provisioning": False,
                },
                {
                    "dataset_id": "DS-003",
                    "tc_ref": "TC-003",
                    "category": "valid",
                    "description": "Feature toggle enabled state",
                    "data": {"toggle_state": "ON", "nbd_design_active": True},
                    "notes": None,
                    "requires_provisioning": False,
                },
                {
                    "dataset_id": "DS-004",
                    "tc_ref": "TC-004",
                    "category": "valid",
                    "description": "Feature toggle disabled state — legacy design",
                    "data": {"toggle_state": "OFF", "nbd_design_active": False},
                    "notes": None,
                    "requires_provisioning": False,
                },
                {
                    "dataset_id": "DS-005",
                    "tc_ref": "TC-005",
                    "category": "invalid",
                    "description": "Invalid state: toggle switches mid-session without proper state management",
                    "data": {
                        "initial_toggle": "OFF",
                        "api_switch_to": "ON",
                        "page_reload_triggered": False,
                    },
                    "notes": "Tests error handling when state sync fails",
                    "requires_provisioning": True,
                },
            ],
        }

    def _mock_review_agent(self, _payload: dict) -> dict:
        """Mock output for Review Agent (Agent 7)."""
        if _payload.get("story_id") == "NGWD6-52184":
            return self._mock_52184_review()
        return {
            "story_id": "NGWD6-50396",
            "quality_score": 88.5,
            "passed_count": 6,
            "flagged_count": 1,
            "auto_fixed_count": 0,
            "findings": [
                {
                    "finding_id": "F-001",
                    "tc_ref": None,
                    "severity": "INFO",
                    "category": "gap",
                    "description": "No explicit test coverage for RTL (Right-to-Left) language support mentioned in NFR",
                    "suggestion": "Add TC-008 for RTL layout verification on Arabic/Hebrew markets",
                    "auto_fixed": False,
                },
                {
                    "finding_id": "F-002",
                    "tc_ref": "TC-005",
                    "severity": "WARNING",
                    "category": "quality",
                    "description": "Step 2 mixes API call with UI state change; should be two separate steps for clarity",
                    "suggestion": "Split into: '2a. Call feature flag API' and '2b. Wait for state sync' for better atomicity",
                    "auto_fixed": False,
                },
            ],
            "gaps_detected": [
                "No explicit accessibility (WCAG 2.1 AA) test case — mentioned in NFR but not covered by TCs",
                "Performance testing missing — '<200ms render time' NFR has no corresponding test",
                "No test for component error state (missing data, malformed JSON)",
            ],
            "duplicate_pairs": [],
        }

    def _mock_reporting_agent(self, _payload: dict) -> dict:
        """Mock output for Reporting Agent (Agent 8)."""
        if _payload.get("story_id") == "NGWD6-52184":
            return self._mock_52184_reporting()
        return {
            "executive_summary": "The NGWD6-50396 Feature Cluster Section story has been analysed and a complete test suite of 7 test cases has been generated, achieving 86% acceptance criteria coverage. The test cases cover happy path, boundary conditions, feature toggle behaviour, and documentation verification. Quality score: 88.5/100. Minor gaps exist in accessibility and performance testing; these require an additional TC-008 for RTL support.",
            "recommendations": [
                "Add TC-008 for RTL (Right-to-Left) language support verification",
                "Add TC-009 for performance profiling (render time < 200ms target)",
                "Consider WCAG 2.1 AA accessibility audit as pre-execution step",
                "Link FIGMA mockups directly in Jira story for visual regression reference",
            ],
        }

    @staticmethod
    def _mock_52184_requirement() -> dict:
        return {
            "story_id": "NGWD6-52184",
            "summary": "[CMS][A11Y][WCAG 2.2] 2.4.11 Focus Not Obscured | Search Layer",
            "component": "CMS",
            "priority": "Major",
            "sprint": "CMS Sprint 278",
            "acceptance_criteria": [
                {"id": "AC-01", "text": "WCAG 2.2 Success Criterion 2.4.11 Focus Not Obscured (Minimum) is met.", "is_ambiguous": False, "ambiguity_note": None, "implicit_assumption": "The approved focus treatment is available for comparison."},
                {"id": "AC-02", "text": "The Search Layer is fully usable without a mouse.", "is_ambiguous": False, "ambiguity_note": None, "implicit_assumption": "Both Classic Search and AI Search are available in the test environment."},
                {"id": "AC-03", "text": "Focus and interactive elements are visually and programmatically perceivable.", "is_ambiguous": False, "ambiguity_note": None, "implicit_assumption": "Browser accessibility-tree inspection is available."},
                {"id": "AC-04", "text": "The solution works across relevant viewports.", "is_ambiguous": False, "ambiguity_note": None, "implicit_assumption": "Desktop, tablet, and mobile viewports are in scope."},
                {"id": "AC-05", "text": "The approved UI/UX focus treatment is applied consistently.", "is_ambiguous": True, "ambiguity_note": "The exact approved focus token and visual specification are not linked in the story.", "implicit_assumption": "The standard site-wide focus treatment is the approval baseline."},
            ],
            "nfr_hints": ["WCAG 2.2 AA accessibility", "Keyboard-only operation", "Responsive behavior", "Screen-reader compatibility"],
            "domain_keywords": ["CMS", "Search Layer", "Classic Search", "AI Search", "WCAG 2.2", "Focus Not Obscured"],
            "clarifying_questions": ["Which approved UI/UX focus specification should be used as the visual baseline?"],
            "overall_risk": "HIGH",
            "confidence_score": 0.94,
        }

    @staticmethod
    def _mock_52184_scenarios() -> dict:
        nodes = [
            ("SN-001", "AC-01", "happy_path", "Classic Search input shows visible, unobscured focus", "Open Classic Search and tab to the input.", "Classic Search is enabled", "Focus indicator is visible and not covered", "HIGH"),
            ("SN-002", "AC-01", "boundary", "AI Search input remains visible at mobile viewport", "Check the focused AI Search input at the narrow mobile breakpoint.", "AI Search is enabled at 375px viewport", "Focused input remains at least partially visible", "HIGH"),
            ("SN-003", "AC-02", "happy_path", "Classic Search is operable by keyboard only", "Open, search, select a result, and close Classic Search without a mouse.", "Classic Search is available", "Keyboard flow completes with logical focus movement", "HIGH"),
            ("SN-004", "AC-02", "alternate_flow", "AI Search is operable by keyboard only", "Perform the equivalent keyboard journey in AI Search.", "AI Search is available", "Keyboard flow completes and focus returns to trigger", "HIGH"),
            ("SN-005", "AC-03", "happy_path", "Focused Search Layer controls expose accessible semantics", "Inspect the focused input and close control in the accessibility tree.", "Browser accessibility tools are available", "Roles, names, and focused state are exposed", "MEDIUM"),
            ("SN-006", "AC-04", "boundary", "Focus treatment is retained across viewports", "Repeat focus checks on desktop, tablet, and mobile.", "Responsive test viewports are available", "No viewport hides, clips, or removes the focus indicator", "HIGH"),
            ("SN-007", "AC-05", "happy_path", "Focus treatment matches approved design", "Compare both search variants against the approved focus specification.", "Approved UI/UX reference is available", "Both variants use the approved consistent treatment", "MEDIUM"),
        ]
        root_nodes = [
            {"node_id": node_id, "ac_ref": ac_ref, "flow_type": flow_type, "title": title, "description": description, "precondition": precondition, "trigger_condition": "Keyboard focus enters the Search Layer", "expected_state": expected_state, "risk_level": risk, "children": []}
            for node_id, ac_ref, flow_type, title, description, precondition, expected_state, risk in nodes
        ]
        return {"story_id": "NGWD6-52184", "total_nodes": 7, "happy_path_count": 4, "alternate_flow_count": 1, "boundary_count": 2, "negative_count": 0, "nfr_count": 0, "root_nodes": root_nodes}

    @staticmethod
    def _mock_52184_test_cases() -> dict:
        test_cases = [
            ("TC-001", "SN-001", "AC-01", "Classic Search input has a visible, unobscured focus indicator", "Validate the Classic Search input focus state against WCAG 2.4.11.", "HIGH", ["accessibility", "happy_path", "keyboard", "classic_search"], ["Classic Search is available", "Approved focus reference is available"], [("Open Classic Search with the keyboard", "The layer opens and focus enters the layer"), ("Tab to the search input", "The input receives a clearly visible focus indicator"), ("Check the input against surrounding overlay and header content", "The focused input is not fully obscured")]),
            ("TC-002", "SN-002", "AC-01", "AI Search focused input remains visible at mobile breakpoint", "Validate focus visibility in AI Search at 375px width.", "HIGH", ["accessibility", "boundary", "responsive", "ai_search"], ["AI Search is available", "Viewport is 375px wide"], [("Open AI Search with the keyboard", "The layer opens"), ("Tab to the search input", "The input receives focus"), ("Inspect focused input at the mobile viewport", "Focus indicator and input remain visible and are not covered")]),
            ("TC-003", "SN-003", "AC-02", "Complete the Classic Search journey using keyboard only", "Validate opening, searching, selecting a result, and closing Classic Search without a mouse.", "HIGH", ["accessibility", "happy_path", "keyboard", "classic_search"], ["Classic Search contains a searchable result"], [("Tab to and activate the Search trigger", "Classic Search opens"), ("Type a valid query and tab to a result", "Results are reachable in logical focus order"), ("Activate a result, reopen Search, and press Escape", "The result opens and closing returns focus to the trigger")]),
            ("TC-004", "SN-004", "AC-02", "Complete the AI Search journey using keyboard only", "Validate the keyboard-only flow in AI Search.", "HIGH", ["accessibility", "alternate_flow", "keyboard", "ai_search"], ["AI Search contains a searchable result"], [("Tab to and activate the AI Search trigger", "AI Search opens"), ("Type a valid query and navigate suggestions or results", "All interactive content is keyboard reachable"), ("Close the layer using Escape or its close control", "Focus returns to the search trigger")]),
            ("TC-005", "SN-005", "AC-03", "Search Layer focus is programmatically perceivable", "Validate semantic exposure of the focused input and close control.", "MEDIUM", ["accessibility", "happy_path", "screen_reader"], ["Browser accessibility tree or screen reader is available"], [("Open each Search Layer variant and focus the input", "Input is focused"), ("Inspect the input in the accessibility tree", "Role, accessible name, and focused state are exposed"), ("Focus the close control and inspect it", "The control has an accessible name and exposed focus")]),
            ("TC-006", "SN-006", "AC-04", "Search Layer focus treatment works across desktop, tablet, and mobile", "Validate both search variants at responsive breakpoints.", "HIGH", ["accessibility", "boundary", "responsive"], ["Desktop, tablet, and mobile viewports are available"], [("Repeat the input focus check at desktop viewport", "Focus is visible and unobscured"), ("Repeat at tablet viewport", "Focus is visible and unobscured"), ("Repeat at mobile viewport", "Focus is visible and unobscured")]),
            ("TC-007", "SN-007", "AC-05", "Classic and AI Search use the approved consistent focus treatment", "Compare focus style with the approved UI/UX reference.", "MEDIUM", ["accessibility", "happy_path", "visual_regression"], ["Approved UI/UX focus specification is available"], [("Focus the Classic Search input and close control", "Focus style matches the approved reference"), ("Focus the AI Search input and close control", "Focus style matches the approved reference"), ("Compare both variants", "No variant uses only the legacy bottom-border treatment")]),
        ]
        return {
            "story_id": "NGWD6-52184",
            "total": len(test_cases),
            "high_risk_count": 5,
            "medium_risk_count": 2,
            "low_risk_count": 0,
            "test_cases": [
                {"tc_id": tc_id, "scenario_node_ref": node_ref, "ac_ref": ac_ref, "title": title, "description": description, "preconditions": preconditions, "steps": [{"step_number": index, "action": action, "expected_result": expected} for index, (action, expected) in enumerate(steps, 1)], "expected_result": steps[-1][1], "risk_level": risk, "tags": tags, "status": "DRAFT", "gherkin": f"Given the Search Layer is available\nWhen a user completes {title.lower()}\nThen the expected accessibility behavior is met"}
                for tc_id, node_ref, ac_ref, title, description, risk, tags, preconditions, steps in test_cases
            ],
        }

    @staticmethod
    def _mock_52184_test_data() -> dict:
        return {
            "story_id": "NGWD6-52184",
            "datasets": [
                {"dataset_id": "DS-001", "tc_ref": "TC-001", "category": "valid", "description": "Classic Search default desktop state", "data": {"search_variant": "classic", "viewport": "desktop", "query": "ID. Buzz"}, "notes": None, "requires_provisioning": False},
                {"dataset_id": "DS-002", "tc_ref": "TC-002", "category": "boundary", "description": "AI Search mobile viewport", "data": {"search_variant": "ai", "viewport_width": 375, "viewport_height": 667, "query": "electric vehicles"}, "notes": None, "requires_provisioning": False},
                {"dataset_id": "DS-003", "tc_ref": "TC-003", "category": "valid", "description": "Classic Search query with a selectable result", "data": {"search_variant": "classic", "query": "Golf", "expected_result_available": True}, "notes": None, "requires_provisioning": False},
                {"dataset_id": "DS-004", "tc_ref": "TC-004", "category": "valid", "description": "AI Search query with suggestions", "data": {"search_variant": "ai", "query": "charging", "expected_suggestion_available": True}, "notes": None, "requires_provisioning": False},
                {"dataset_id": "DS-005", "tc_ref": "TC-006", "category": "boundary", "description": "Responsive viewport matrix", "data": {"desktop_width": 1280, "tablet_width": 768, "mobile_width": 375}, "notes": None, "requires_provisioning": False},
                {"dataset_id": "DS-006", "tc_ref": "TC-007", "category": "valid", "description": "Approved focus style reference", "data": {"reference": "Approved site-wide UI/UX focus treatment"}, "notes": "Confirm the final design token with UI/UX.", "requires_provisioning": True},
            ],
        }

    @staticmethod
    def _mock_52184_review() -> dict:
        return {
            "story_id": "NGWD6-52184", "quality_score": 92.0, "passed_count": 7, "flagged_count": 0, "auto_fixed_count": 0,
            "findings": [{"finding_id": "F-001", "tc_ref": "TC-007", "severity": "INFO", "category": "gap", "description": "The Jira ticket requires a UI/UX focus treatment but does not link the final specification.", "suggestion": "Attach or link the approved Figma focus token before final execution.", "auto_fixed": False}],
            "gaps_detected": ["Confirm the approved UI/UX focus specification before final execution."], "duplicate_pairs": [],
        }

    @staticmethod
    def _mock_52184_reporting() -> dict:
        return {
            "executive_summary": "NGWD6-52184 has been analysed into seven risk-based accessibility test cases for the Search Layer. The suite covers WCAG 2.4.11 focus visibility, keyboard-only operation in Classic and AI Search, programmatic focus perception, responsive behavior, and consistent UI/UX focus treatment.",
            "recommendations": ["Confirm the approved UI/UX focus specification before execution.", "Execute keyboard and accessibility-tree checks in both Classic Search and AI Search.", "Record evidence at desktop, tablet, and mobile viewports."],
        }


class MockChain:
    """Mock LangChain-compatible chain that mimics the real invoke() interface."""

    def __init__(self, mock_llm: MockLLM):
        self.mock_llm = mock_llm

    def invoke(self, payload: dict) -> dict:
        return self.mock_llm.invoke(payload)
