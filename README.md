# KI Testcase Generator

Analyzes a Jira user story exported as XML and generates a structured Word document containing test cases, following the standard test case template.

You can use it in two ways:
- OpenAI API mode (automatic generation)
- Copilot-assisted mode (no API key, uses this VS Code chat)

There is now also a full end-to-end mode from Jira link:
- Jira link -> fetch issue via Jira API -> generate test cases -> create Word document

## Setup

1. **Install dependencies** (uses the shared venv at the root):
   ```
   pip install -r requirements.txt
   ```

2. **Configure API key** (only for OpenAI API mode):
   ```
   copy config.example.json config.json
   ```
   Then open `config.json` and replace `sk-YOUR-OPENAI-API-KEY-HERE` with your actual OpenAI API key.

   Available models (set in `config.json`):
   | Model | Notes |
   |---|---|
   | `gpt-4o` | Best quality, recommended |
   | `gpt-4o-mini` | Faster, cheaper |

## Usage

```
python generate_testcases.py <path-to-jira-export.xml>
```

## Fully automatic from Jira link

Use this mode when you want one command from a Jira URL to a Markdown document.

1. Update config with both OpenAI and Jira credentials.
2. Run:

```
python jira_to_testcases.py --jira-link https://vwgroup-b2b.atlassian.net/browse/NGWD6-49603
```

Output is saved as `output/<ISSUE_KEY>_testcases_functional.md`.

No AI API available? Use rule-based mode:

```
python jira_to_testcases.py --jira-link https://vwgroup-b2b.atlassian.net/browse/NGWD6-49603 --mode rule-based
```

`--mode auto` is the default and will try OpenAI first, then fallback to rule-based automatically.

Optional custom output path:

```
python jira_to_testcases.py --jira-link https://vwgroup-b2b.atlassian.net/browse/NGWD6-49603 --output output/NGWD6-49603_testcases.md
```

Optional debug dump of parsed story:

```
python jira_to_testcases.py --jira-link https://vwgroup-b2b.atlassian.net/browse/NGWD6-49603 --dump-story output/story.json
```

## Copilot-assisted mode (no API key)

If you want to use the AI in this VS Code window instead of API keys:

1. Generate a prompt file from XML:
   ```
   python generate_testcases.py data/NGWD6-49603.xml --emit-prompt output/prompt.txt
   ```
2. Open `output/prompt.txt`, copy all text, paste it into Copilot chat.
3. Ask Copilot to return only JSON.
4. Save that JSON into a file, for example `output/testcases.json`.
5. Build the Word document from JSON:
   ```
   python generate_testcases.py data/NGWD6-49603.xml --from-json output/testcases.json
   ```

This creates the same `.docx` output without requiring an OpenAI key.

The generated `.docx` is written to the `output/` folder, named after the Jira key (e.g. `output/NGWD6-49603.docx`).

## Shared Copilot Skill (Markdown-first workflow)

For team-wide usage, this repository now includes a reusable Copilot skill for
Jira/Confluence-based testcase review and generation with Markdown outputs:

- Skill definition: `../.github/skills/Template_Testcases/SKILL.md`
- Guide (German): `../.github/skills/Template_Testcases/README_DE.md`
- Guide (English): `../.github/skills/Template_Testcases/README_EN.md`
- Output template: `../.github/skills/Template_Testcases/templates/testcase_output_template.md`

Typical workflow:
1. Generate testcase review Markdown (`<ISSUE_KEY>_testcase-review.md`).
2. Generate final testcase Markdown (`<ISSUE_KEY>_testcases.md`).
3. Validate in Markdown preview and optionally export to PDF.

Direct mode (no review step):
1. Ask Copilot to generate testcases directly for a Jira key.
2. Save as `output/<ISSUE_KEY>_testcases_direct.md`.

Recommended output folder: `output/`

## KI Fast Path (Skill-First)

Damit eine KI nicht jedes Mal die komplette Datei lesen muss, nutze diesen Ablauf:

1. Bei Testfallerstellung/-review immer zuerst den Shared Copilot Skill verwenden.
2. Zuerst nur Struktur lesen (Ueberschriften, AC-Block, bestehende Output-Datei), nicht den kompletten Inhalt.
3. Danach nur die relevanten Abschnitte nachladen (Ticket-AC, Szenario, erwartetes Output-Format).
4. Bestehende Muster aus `output/*_testcases*.md` wiederverwenden statt neue Struktur zu erfinden.
5. Kontextaufnahme sofort stoppen, sobald AC + Scope + Format eindeutig sind.
6. Markdown-first arbeiten; nur bei explizitem Wunsch auf andere Artefakte wechseln.
7. Vor Abschluss immer gegen Scope pruefen: AC-Abdeckung, In-Scope/Out-of-Scope, Traceability.

Kurzregel: Skill first, targeted reads second, generate third.

**Custom output path:**
```
python generate_testcases.py data/NGWD6-49603.xml --output my_testcases.docx
```

## Input XML format

Export the Jira issue as XML (RSS format) from the Jira issue page:
*Share → Export XML* or append `?format=rss` to the issue URL.

The script extracts:
- Issue key & summary
- Jira URL
- Description (User Story + Acceptance Criteria)
- Component, priority, status

## Output document structure

The generated `.docx` follows the standard template:

```
Heading 1  – Test Cases – <Feature>
Heading 2  – <Feature>
Heading 2  – User story: <KEY> <Summary>
Heading 2  – URL: <Jira link>

            Test scenario / Description / AC bullets

Heading 3  – Test Case 1 – <Title>
             Description / Preconditions / Test Steps / Expected Result / Test Results

Heading 3  – Test Case 2 – ...
...
```

## Folder structure

```
KI_Tetscases/
├── data/
│   ├── NGWD6-45733_Sample_Testcase.docx   ← word template reference
│   └── NGWD6-49603.xml                    ← example Jira XML input
├── output/                                ← generated documents (auto-created)
├── generate_testcases.py                  ← main script
├── config.json                            ← your API key (not committed)
├── config.example.json                    ← config template
├── requirements.txt
└── README.md
```
