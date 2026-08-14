---
name: stratguide-scribe
description: Break down story scenes into structured "blob" sequences in a video-game-guidebook style, and write individual blobs. Use when the user mentions "stratguide", "guidebook", "blob outline", or asks to structure a scene/chapter/story into a sequence of blobs. Also trigger when the user asks to write or revise content in any individual blob style (e.g., "write the action blobs").
---

# Stratguide Scribe

Structure stories and scenes as sequences of typed "blobs" — short text blocks in one of five distinct styles, arranged like entries in a video-game strategy guide.

## Blob Styles (quick reference)

| Style | Voice / POV | One-liner |
|---|---|---|
| **Action** | 2nd person, guidebook tone | How-to instructions, like a boss walkthrough. Illusion of choice. |
| **Narrator** | 1st person address, omniscient | Spoken exposition from an all-knowing narrator. |
| **Description** | 2nd person, prose fiction | Regular fiction prose, but "you" is the protagonist. |
| **Dialogue** | 3rd person character speech | Four short bullet-point lines from a single NPC. Never the main character. |
| **Table** | Structured list | Items, locations, choices, traps — any game mechanic. Sizes: 2, 3, 4, 9, 12. |

## Mode Detection

**STOP:** This is a branching skill. The modes below are mutually exclusive. Read ONLY the ONE reference file for the detected mode. NEVER read any other files.

Determine mode from user request:

**Breakdown mode**:
- Triggers: "break down", "breakdown", "blob outline", "structure this scene", "stratguide", "guidebook", "game guide book", or any request to outline/plan a scene as a blob sequence
- **Read**: `references/breakdown-reference.md`

**Action mode**:
- Triggers: "write the action blobs", "action mode", "action style", or user provides a breakdown and asks for Action blobs to be written
- **Read**: `references/action-reference.md`

**Narrator mode**:
- Triggers: "write the narrator blobs", "narrator mode", "narrator style", or user provides a breakdown and asks for Narrator blobs to be written
- **Read**: `references/narrator-reference.md`

**Description mode**:
- Triggers: "write the description blobs", "description mode", "description style", or user provides a breakdown and asks for Description blobs to be written
- **Read**: `references/description-reference.md`

**Dialogue mode**:
- Triggers: "write the dialogue blobs", "dialogue mode", "dialogue style", or user provides a breakdown and asks for Dialogue blobs to be written
- **Read**: `references/dialogue-reference.md`

**Table mode**:
- Triggers: "write the table blobs", "table mode", "table style", or user provides a breakdown and asks for Table blobs to be written
- **Read**: `references/table-reference.md`

If ambiguous, ask user which mode.

**REMINDER:** Each mode is a SEPARATE BRANCH. Read ONLY the single reference file listed for the detected mode. Do NOT read files for other modes.

## Workflow

1. Detect mode from triggers above
2. Read the appropriate reference doc for that mode
3. Follow the workflow in that reference doc
4. Present completed output to user
