# Test Cases — NGWD6-52184

> **Story:** [CMS][A11Y][WCAG 2.2] 2.4.11 Focus Not Obscured | Search Layer  
> **Component:** CMS  
> **Priority:** Major  
> **Sprint:** CMS Sprint 278  
> **Generated:** 2026-08-19 14:41 UTC  
> **Coverage:** 50.0%  
> **Quality Score:** 92/100  

---

## Executive Summary

NGWD6-52184 has been analysed into seven risk-based accessibility test cases for the Search Layer. The suite covers WCAG 2.4.11 focus visibility, keyboard-only operation in Classic and AI Search, programmatic focus perception, responsive behavior, and consistent UI/UX focus treatment.

---

## Test Cases (7 total)

### TC-001 — Classic Search input has a visible, unobscured focus indicator

**Risk:** HIGH  
**AC Reference:** AC-01  
**Tags:** accessibility, happy_path, keyboard, classic_search  

**Description:** Validate the Classic Search input focus state against WCAG 2.4.11.

**Preconditions:**
- Classic Search is available
- Approved focus reference is available

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open Classic Search with the keyboard | The layer opens and focus enters the layer |
| 2 | Tab to the search input | The input receives a clearly visible focus indicator |
| 3 | Check the input against surrounding overlay and header content | The focused input is not fully obscured |

**Overall Expected Result:** The focused input is not fully obscured

**Gherkin:**
```gherkin
Given the Search Layer is available
When a user completes classic search input has a visible, unobscured focus indicator
Then the expected accessibility behavior is met
```

---

### TC-002 — AI Search focused input remains visible at mobile breakpoint

**Risk:** HIGH  
**AC Reference:** AC-01  
**Tags:** accessibility, boundary, responsive, ai_search  

**Description:** Validate focus visibility in AI Search at 375px width.

**Preconditions:**
- AI Search is available
- Viewport is 375px wide

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open AI Search with the keyboard | The layer opens |
| 2 | Tab to the search input | The input receives focus |
| 3 | Inspect focused input at the mobile viewport | Focus indicator and input remain visible and are not covered |

**Overall Expected Result:** Focus indicator and input remain visible and are not covered

**Gherkin:**
```gherkin
Given the Search Layer is available
When a user completes ai search focused input remains visible at mobile breakpoint
Then the expected accessibility behavior is met
```

---

### TC-003 — Complete the Classic Search journey using keyboard only

**Risk:** HIGH  
**AC Reference:** AC-02  
**Tags:** accessibility, happy_path, keyboard, classic_search  

**Description:** Validate opening, searching, selecting a result, and closing Classic Search without a mouse.

**Preconditions:**
- Classic Search contains a searchable result

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Tab to and activate the Search trigger | Classic Search opens |
| 2 | Type a valid query and tab to a result | Results are reachable in logical focus order |
| 3 | Activate a result, reopen Search, and press Escape | The result opens and closing returns focus to the trigger |

**Overall Expected Result:** The result opens and closing returns focus to the trigger

**Gherkin:**
```gherkin
Given the Search Layer is available
When a user completes complete the classic search journey using keyboard only
Then the expected accessibility behavior is met
```

---

### TC-004 — Complete the AI Search journey using keyboard only

**Risk:** HIGH  
**AC Reference:** AC-02  
**Tags:** accessibility, alternate_flow, keyboard, ai_search  

**Description:** Validate the keyboard-only flow in AI Search.

**Preconditions:**
- AI Search contains a searchable result

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Tab to and activate the AI Search trigger | AI Search opens |
| 2 | Type a valid query and navigate suggestions or results | All interactive content is keyboard reachable |
| 3 | Close the layer using Escape or its close control | Focus returns to the search trigger |

**Overall Expected Result:** Focus returns to the search trigger

**Gherkin:**
```gherkin
Given the Search Layer is available
When a user completes complete the ai search journey using keyboard only
Then the expected accessibility behavior is met
```

---

### TC-005 — Search Layer focus is programmatically perceivable

**Risk:** MEDIUM  
**AC Reference:** AC-03  
**Tags:** accessibility, happy_path, screen_reader  

**Description:** Validate semantic exposure of the focused input and close control.

**Preconditions:**
- Browser accessibility tree or screen reader is available

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open each Search Layer variant and focus the input | Input is focused |
| 2 | Inspect the input in the accessibility tree | Role, accessible name, and focused state are exposed |
| 3 | Focus the close control and inspect it | The control has an accessible name and exposed focus |

**Overall Expected Result:** The control has an accessible name and exposed focus

**Gherkin:**
```gherkin
Given the Search Layer is available
When a user completes search layer focus is programmatically perceivable
Then the expected accessibility behavior is met
```

---

### TC-006 — Search Layer focus treatment works across desktop, tablet, and mobile

**Risk:** HIGH  
**AC Reference:** AC-04  
**Tags:** accessibility, boundary, responsive  

**Description:** Validate both search variants at responsive breakpoints.

**Preconditions:**
- Desktop, tablet, and mobile viewports are available

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Repeat the input focus check at desktop viewport | Focus is visible and unobscured |
| 2 | Repeat at tablet viewport | Focus is visible and unobscured |
| 3 | Repeat at mobile viewport | Focus is visible and unobscured |

**Overall Expected Result:** Focus is visible and unobscured

**Gherkin:**
```gherkin
Given the Search Layer is available
When a user completes search layer focus treatment works across desktop, tablet, and mobile
Then the expected accessibility behavior is met
```

---

### TC-007 — Classic and AI Search use the approved consistent focus treatment

**Risk:** MEDIUM  
**AC Reference:** AC-05  
**Tags:** accessibility, happy_path, visual_regression  

**Description:** Compare focus style with the approved UI/UX reference.

**Preconditions:**
- Approved UI/UX focus specification is available

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Focus the Classic Search input and close control | Focus style matches the approved reference |
| 2 | Focus the AI Search input and close control | Focus style matches the approved reference |
| 3 | Compare both variants | No variant uses only the legacy bottom-border treatment |

**Overall Expected Result:** No variant uses only the legacy bottom-border treatment

**Gherkin:**
```gherkin
Given the Search Layer is available
When a user completes classic and ai search use the approved consistent focus treatment
Then the expected accessibility behavior is met
```

---

## Coverage Summary

| Acceptance Criterion | Coverage | Test Cases |
|---------------------|----------|------------|
| AC-01 — WCAG 2.2 Success Criterion 2.4.11 Focus Not Obscured (Minimu | 67% | TC-001, TC-002 |
| AC-02 — The Search Layer is fully usable without a mouse. | 50% | TC-003, TC-004 |
| AC-03 — Focus and interactive elements are visually and programmatic | 33% | TC-005 |
| AC-04 — The solution works across relevant viewports. | 33% | TC-006 |
| AC-05 — The approved UI/UX focus treatment is applied consistently. | 33% | TC-007 |

## Recommendations

- Confirm the approved UI/UX focus specification before execution.
- Execute keyboard and accessibility-tree checks in both Classic Search and AI Search.
- Record evidence at desktop, tablet, and mobile viewports.
