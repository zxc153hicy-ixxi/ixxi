---
name: black-book
description: Break down story scenes into structured "blob" sequences in a 'black book' style, and write individual blob styles from existing breakdowns. Use when the user mentions "black book", "necromancer story", "grimiore", "black book outline", or "black book blobs". Also trigger when the user asks to write or revise content in any individual blob style ('verse', 'essay', 'interview', 'epitaph', or 'lemma' blobs) for an existing breakdown.
---

# Black Book

Structure stories and scenes as sequences of typed "blobs" — short text blocks in one of five distinct styles, arranged like entries in a necromancer's grimiore, or "Black Book".

## Blob Styles (quick reference)

| Style | Voice / POV | One-liner |
|---|---|---|
| **Verse** | 1st-person, action scrawls | Like a string of action-focused texts from a scholarly, eloquent necromancer. |
| **Essay** | discursive 1st-person | Like a serious nonfiction essay, but describes/argues a specific fiction element.  |
| **Interview** | candid, conversational 1st-person | A framed monologue where prompts stand in for the interviewer. |
| **Memorials** | formal, compressed 2nd/3rd-person | 2-4 memorials. Aimed at honoring the dead or addressing passers-by. |
| **Lemma** | 3rd-person omniscient | Encyclopedia entry for a fictional element: items, locations, monsters, etc. |

## Mode Detection

**STOP:** This is a branching skill. The modes below are mutually exclusive. Read ONLY the ONE reference file for the detected mode. NEVER read any other files.

Determine mode from user request:

**Breakdown mode**:
- Triggers: "break down", "breakdown", "blob outline", "structure this scene", or any request to outline/plan a scene as a blob sequence
- **Read**: `references/breakdown-reference.md`

**Verse mode**:
- Triggers: "write verse blobs", "verse mode", "draft the verses", "generate verse blob(s)", or any request to write Verse-style content for an existing breakdown
- **Read**: `references/verse-reference.md`

**Essay mode**:
- Triggers: "write essay blobs", "essay mode", "draft the essays", "generate essay blob(s)", or any request to write Essay-style content for an existing breakdown
- **Read**: `references/essay-reference.md`

**Interview mode**:
- Triggers: "write interview blobs", "interview mode", "draft the interviews", "generate interview blob(s)", or any request to write Interview-style content for an existing breakdown
- **Read**: `references/interview-reference.md`

**Memorials mode**:
- Triggers: "write memorials", "write memorial blobs", "memorials mode", "draft the memorials", "generate memorial blob(s)", "write the epitaphs", or any request to write Memorials-style content for an existing breakdown
- **Read**: `references/memorials-reference.md`

**Lemma mode**:
- Triggers: "write lemma blobs", "lemma mode", "draft the lemmas", "generate lemma blob(s)", "write the encyclopedia entries", or any request to write Lemma-style content for an existing breakdown
- **Read**: `references/lemma-reference.md`

If ambiguous, ask user which mode.

**REMINDER:** Each mode is a SEPARATE BRANCH. Read ONLY the single reference file listed for the detected mode. Do NOT read files for other modes.

## Workflow

1. Detect mode from triggers above
2. Read the appropriate reference doc for that mode
3. Follow the workflow in that reference doc
4. Present completed output to user
