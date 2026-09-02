---
applyTo: "**"
description: "Global agent instructions for testcase workflows: prefer Copilot skill, use selective reading, avoid overengineering, and define verifiable success criteria."
---

# Agent-guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, or refactoring code to avoid overcomplication, make surgical changes, surface assumptions, and define verifiable success criteria.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## Testcase Workflow Priority

- For testcase creation or testcase review requests, always prefer the shared Copilot skill workflow first.
- Use Markdown-first outputs for testcase artifacts unless explicitly requested otherwise.
- If the skill/template is unavailable in the current workspace, state that and fall back to the closest existing repository pattern.

## Context Efficiency (Do Not Read Everything)

- Do not read full files by default.
- First gather structure, then read only relevant sections.
- Prefer targeted reads of the exact headings/blocks needed for the task.
- Reuse known file patterns from existing testcase outputs before reading additional files.
- Stop context gathering once acceptance criteria and output format are clear.

## 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; do not pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what is confusing, and ask.

## 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that was not requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask: Would a senior engineer call this overcomplicated? If yes, simplify.

## 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:

- Do not improve adjacent code/comments/formatting unless required.
- Do not refactor unrelated areas.
- Match existing style.
- If unrelated dead code is found, mention it; do not delete it unless asked.

When your changes create orphans:

- Remove imports/variables/functions made unused by your own changes.
- Do not remove pre-existing dead code unless requested.

Test: Every changed line should trace directly to the user request.

## 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

- Add validation -> write tests for invalid inputs, then make them pass.
- Fix bug -> reproduce with a test, then make it pass.
- Refactor X -> tests pass before and after.

For multi-step tasks, state a brief plan with verification:

1. Step -> verify with a concrete check.
2. Step -> verify with a concrete check.
3. Step -> verify with a concrete check.

Strong success criteria enable independent execution.

## 5. Linter and Formatter First

Let tools handle style. Do not spend effort on manual formatting.

- Rely on project linter/formatter for style.
- Treat VS Code Problems panel warnings/errors as actionable before completion.
- If no linter/formatter is configured, inform the user and suggest setup.
- Keep diffs focused on logic, not whitespace/style preference.
