---
name: character-analysis
description: Analyze fictional characters using structured templates. Use when asked to analyze, break down, or create character profiles for fictional characters. Triggers include "analyze [character]", "character breakdown", "create character templates", or requests for character analysis documents.
---

# Character Analysis

Analyze fictional characters and output structured documents.

## Mode Detection

**STOP:** This is a branching skill, not a workflow. The four modes below are mutually exclusive. Read ONLY the ONE reference file for the detected mode. NEVER read any other files.

Determine mode from user request:

**Profile mode**:
- Triggers: "analyze", "full analysis", "character profile", "character template"
- **Read**: `references/profile-reference.md`

**Description mode**:
- Triggers: "character description", "describe [character]", "what does [character] look like", "physical description", "appearance"
- **Read**: `references/description-reference.md`

**Actions mode**:
- Triggers: "character actions", "what does [character] do", "list of actions", "action list"
- **Read**: `references/actions-reference.md`

**Quotes mode**:
- Triggers: "character quotes", "what are [character]'s maxims", "list of sayings", "quotes list"
- **Read**: `references/quotes-reference.md`

If ambiguous, ask user which mode.

**REMINDER:** Each mode is a SEPARATE BRANCH. Read ONLY the single reference file listed for the detected mode. Do NOT read files for other modes.  

## Workflow

1. Detect mode from triggers above
2. Read the appropriate reference doc for that mode
3. Follow the workflow in that reference doc
4. Present completed file(s) to user

**REMINDER:** NEVER DO ALL FOUR MODES. Never, ever assume the user wants this. You **MUST** pick and run one mode.