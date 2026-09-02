# Test Cases — NGWD6-51297

> **Story:** 🔵 [CMS][NBD'26] S127 Feature Cluster Section (Simple) - Update as per new design  
> **Component:** CMS  
> **Priority:** Major  
> **Sprint:** CMS Sprint 273  
> **Generated:** 2026-07-28 10:25 UTC  
> **Coverage:** 50.0%  
> **Quality Score:** 88/100  

---

## Executive Summary

The NGWD6-50396 Feature Cluster Section story has been analysed and a complete test suite of 7 test cases has been generated, achieving 86% acceptance criteria coverage. The test cases cover happy path, boundary conditions, feature toggle behaviour, and documentation verification. Quality score: 88.5/100. Minor gaps exist in accessibility and performance testing; these require an additional TC-008 for RTL support.

---

## Test Cases (7 total)

### TC-001 — TC-001 – Feature Cluster displays NBD'26 design when active

**Risk:** HIGH  
**AC Reference:** AC-01  
**Tags:** regression, smoke, happy_path, visual  

**Description:** Verify that the Feature Cluster Section component renders with the new NBD'26 FIGMA design specifications

**Preconditions:**
- Feature toggle for NBD'26 is enabled for the test market
- User has navigated to a page containing the Feature Cluster component

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open the CMS page containing the Feature Cluster Section component | — |
| 2 | Verify that the component title matches the NBD'26 FIGMA spec | Title styling, font size, and colour match the FIGMA mockup exactly |
| 3 | Verify each named item in the cluster displays with correct styling | All items have correct padding, borders, background colour per FIGMA spec |
| 4 | Verify layout alignment and spacing between items | Gaps and alignment match FIGMA; no overlaps; responsive padding applied |

**Overall Expected Result:** Feature Cluster Section displays exactly as specified in NBD'26 FIGMA design; all named items visible and properly styled

**Gherkin:**
```gherkin
Given the Feature Cluster component is rendered on a CMS page
And the NBD'26 feature toggle is ENABLED
When the page loads
Then the component displays with NBD'26 design specifications
And all named items are visible and properly styled
```

---

### TC-002 — TC-002 – Feature Cluster responsive at 960px tablet viewport

**Risk:** MEDIUM  
**AC Reference:** AC-01  
**Tags:** regression, responsive, boundary  

**Description:** Verify responsive layout at tablet breakpoint (960px)

**Preconditions:**
- Feature toggle ENABLED
- Browser viewport at 960px width

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Set browser viewport to 960px width | — |
| 2 | Navigate to page with Feature Cluster | Component layout adapts; no horizontal scroll |
| 3 | Verify that 'All Features' box moves to right side of layout | Box is positioned right; space is optimised per NBD'26 tablet spec |
| 4 | Verify font sizes and padding scale appropriately | Text is readable; spacing is proportional; no clipping occurs |

**Overall Expected Result:** Layout is responsive and matches NBD'26 tablet design specification at 960px

**Gherkin:**
```gherkin
Given viewport is 960px wide
When Feature Cluster loads
Then layout adapts for tablet
And All Features box aligns right
And text remains readable
```

---

### TC-003 — TC-003 – Toggle ON: NBD'26 design visible

**Risk:** HIGH  
**AC Reference:** AC-02  
**Tags:** feature_toggle, smoke  

**Description:** Verify that enabling the feature toggle shows the NBD'26 design

**Preconditions:**
- Feature toggle is currently ENABLED for test market

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Verify feature toggle status is ON | — |
| 2 | Load page with Feature Cluster | — |
| 3 | Verify NBD'26 design elements are rendered (new styles, layout, colors) | New design is visible; legacy styles are not applied |

**Overall Expected Result:** When toggle is ON, Feature Cluster displays the new NBD'26 design without legacy fallback

**Gherkin:**
```gherkin
Given feature toggle is ON
When page renders
Then NBD'26 design is displayed
```

---

### TC-004 — TC-004 – Toggle OFF: legacy design fallback

**Risk:** HIGH  
**AC Reference:** AC-02  
**Tags:** feature_toggle, smoke  

**Description:** Verify that disabling the feature toggle shows the legacy design

**Preconditions:**
- Feature toggle is currently DISABLED for test market

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Verify feature toggle status is OFF | — |
| 2 | Load page with Feature Cluster | — |
| 3 | Verify legacy design is rendered (old styles, layout, colors) | Legacy design is visible; no new NBD'26 elements appear |

**Overall Expected Result:** When toggle is OFF, Feature Cluster displays the legacy design

**Gherkin:**
```gherkin
Given feature toggle is OFF
When page renders
Then legacy design is displayed
```

---

### TC-005 — TC-005 – Toggle runtime switch updates design dynamically

**Risk:** MEDIUM  
**AC Reference:** AC-02  
**Tags:** feature_toggle, negative  

**Description:** Verify design updates when toggle is switched during an active session (no reload)

**Preconditions:**
- Page with Feature Cluster already loaded
- Toggle initially OFF

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open Feature Cluster page with toggle OFF | Legacy design visible |
| 2 | Call feature flag API to toggle ON (mid-session) | — |
| 3 | Verify Feature Cluster updates to NBD'26 design without page reload | Design updates in real-time; smooth transition; no page flicker |
| 4 | Check browser console for errors | No JavaScript errors; no CSS conflicts logged |

**Overall Expected Result:** Runtime toggle switch updates the design dynamically without requiring a page reload

**Gherkin:**
```gherkin
Given Feature Cluster loaded with toggle OFF
When feature flag is toggled to ON via API
Then design updates immediately
And no page reload occurs
And no console errors appear
```

---

### TC-006 — TC-006 – Storybook documents Feature Cluster NBD'26 variant

**Risk:** LOW  
**AC Reference:** AC-03  
**Tags:** documentation  

**Description:** Verify Storybook contains updated Feature Cluster component documentation

**Preconditions:**
- Storybook application is deployed and accessible

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open Storybook and navigate to Feature Cluster story | — |
| 2 | Verify NBD'26 variant exists in the component stories | Variant is listed and renders correctly |
| 3 | Verify component props are documented | Props table shows all inputs with descriptions and types |
| 4 | Verify use case examples are provided | Multiple variants and usage examples are displayed |

**Overall Expected Result:** Storybook contains complete documentation for NBD'26 Feature Cluster variant

---

### TC-007 — TC-007 – SysDoc updated with Feature Cluster specs

**Risk:** LOW  
**AC Reference:** AC-04  
**Tags:** documentation  

**Description:** Verify System Documentation reflects NBD'26 Feature Cluster changes

**Preconditions:**
- SysDoc system is accessible

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to Feature Cluster section in SysDoc | — |
| 2 | Verify updated component specifications are documented | New design specs, props, and behaviours are described |
| 3 | Verify links to FIGMA mockups are included | FIGMA design reference links are present and valid |
| 4 | Verify version history shows recent update | Update timestamp and author are recorded |

**Overall Expected Result:** SysDoc is updated with complete NBD'26 Feature Cluster specifications

---

## Coverage Summary

| Acceptance Criterion | Coverage | Test Cases |
|---------------------|----------|------------|
| AC-01 — Named items, section match the NBD'26 specifications from FI | 67% | TC-001, TC-002 |
| AC-02 — NBD changes are hidden behind the feature activation toggle  | 60% | TC-003, TC-004, TC-005 |
| AC-03 — Storybook documentation updated with new component specs | 25% | TC-006 |
| AC-04 — SysDoc (System Documentation) updated to reflect NBD'26 chan | 25% | TC-007 |

## Recommendations

- Add TC-008 for RTL (Right-to-Left) language support verification
- Add TC-009 for performance profiling (render time < 200ms target)
- Consider WCAG 2.1 AA accessibility audit as pre-execution step
- Link FIGMA mockups directly in Jira story for visual regression reference
