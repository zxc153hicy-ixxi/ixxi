---
name: prose-producer
description: Orchestrates a full scene draft. Given a full story outline, generates a scene brief, produces a scene frame document with style cards, composes the scene, audits it for story fit and internal quality, and optionally applies chosen fixes. Triggers include "produce a scene", "run the prose pipeline", "prose-producer".
---

# Prose Producer

Multi-stage orchestrator. User provides:
- `STORY_PATH` — full story outline
- `PRIOR_SCENE_PATH` — prior scene's prose file (omit / leave empty if this is scene 1)
- `SOURCE_PATH` — source style passage(s)
- `SCENE_TAG` — identifier for the scene to produce (e.g., scene number or label, like "Scene 2" or "dreamreel-s2")

## Setup

1. Verify `STORY_PATH` and `SOURCE_PATH` exist. Halt and report if missing.
2. If `PRIOR_SCENE_PATH` was provided, verify it exists. If not provided, treat as scene 1.
3. Confirm `SCENE_TAG` with the user if it isn't unambiguous from the inputs.
4. Detect **interactive mode**: if the user's invoking message contains phrases like "interactive", "interactive mode", "pause between stages", or similar, set `INTERACTIVE = true`. Otherwise `INTERACTIVE = false`.

If at any stage a subagent fails or expected output files are missing, halt immediately and report the failure to the user.

## Interactive Mode

When `INTERACTIVE = true`, after each of Stages 1–4 completes, **pause** before launching the next stage. Print:
- The path of the file just produced
- A short prompt instructing the user they can edit the file directly, then respond with one of:
  - `redo with: <feedback>` — re-run the just-completed stage with `<feedback>` appended as extra instructions; replace the captured path with whatever the rerun returns; pause again after it completes
  - `continue` — proceed to the next stage as normal
  - `continue with note: <note>` — proceed to the next stage, appending `<note>` as additional instructions/context to that stage's prompt only (notes do not carry past one stage)

Apply pauses only after Stages 1, 2, 3, and 4.

When `INTERACTIVE = false`, run all stages back-to-back as described below with no intermediate user input.

## Prompt files

Most stages' agent prompts live in their own files under `references/`. For each subagent stage: read the prompt file, substitute the placeholders (e.g. `{STORY_PATH}`, `{SCENE_TAG}`, `{SCENE_FRAME_PATH}`) with the actual values captured so far, and pass the resulting text to the subagent.

Stage 3 is the exception — it runs in your context (no subagent) by following the `scene-writer` skill directly. See its section below.

## Stage 1 — Scene Brief (opus)

Launch a `general-purpose` subagent with `model: opus`. Prompt: `references/stage1-brief.md`.

Substitute `{STORY_PATH}`, `{PRIOR_SCENE_PATH}`, `{SCENE_TAG}`.

Capture the returned path as `SCENE_BRIEF_PATH`.

## Stage 2 — Scene Frame (sonnet)

Launch a `general-purpose` subagent with `model: sonnet`. Prompt: `references/stage2-cards.md`.

Substitute `{SCENE_BRIEF_PATH}`, `{SOURCE_PATH}`, `{SCENE_TAG}`.

Capture the returned scene-frame path as `SCENE_FRAME_PATH`.

## Stage 3 — Compose (inline; spawns sonnet phase agents)

Do NOT launch a subagent for this stage. The `scene-writer` skill orchestrates four phase subagents itself, and a subagent cannot spawn its own subagents — so this stage runs in YOUR context.

Follow `.claude/skills/scene-writer/SKILL.md` directly:
- `INPUT_PATHS` = [`{SCENE_BRIEF_PATH}`, `{SCENE_FRAME_PATH}`]. Do not pass the full story outline, source style passage, or prior scene file — Agents are constrained to the brief and frame.
- `STORYNAME`, `SCENE_NUM`, `WORDCOUNT` come from the scene brief (or the values you captured during Setup).
- Write all output files under `output/`.

Treat every section of the scene frame as binding constraints throughout drafting. Do not re-describe material listed under "Already Rendered (DO NOT RE-DESCRIBE)" in the scene brief.

When scene-writer completes, capture the final scene file path as `SCENE_DRAFT_PATH`.

Interactive-mode pause (if `INTERACTIVE = true`) happens AFTER the full 4-phase composition finishes, not between phases.

## Stage 4 — Review (opus)

Launch a `general-purpose` subagent with `model: opus`. Prompt: `references/stage4-review.md`.

Substitute `{SCENE_DRAFT_PATH}`, `{SCENE_BRIEF_PATH}`, `{SCENE_FRAME_PATH}`.

Capture the returned post-scene summary path as `POST_SCENE_SUMMARY_PATH`. The scene draft path is unchanged (revised in place).

## Stage 5 — Audit (sonnet)

Launch a `general-purpose` subagent with `model: sonnet`. Prompt: `references/stage5-audit.md`.

Substitute `{SCENE_DRAFT_PATH}`, `{STORY_PATH}`, `{PRIOR_SCENE_PATH}`, `{SCENE_TAG}`.

Capture the returned audit card path.

## Review with User

Read the audit card yourself. Present the two lists (Story Fit, Internal Quality) to the user and ask which items, if any, they want applied to the scene draft. Accept their selections in any reasonable form (numbers, ranges, "all", "none", free-form).

If the user picks **none**, skip Stage 6 and go to Final Output.

## Stage 6 — Apply Fixes (sonnet, optional)

Only run if the user picked one or more fixes.

Launch a `general-purpose` subagent with `model: sonnet`. Prompt: `references/stage6-apply-fixes.md`.

Substitute `{SCENE_DRAFT_PATH}` and `{CHOSEN_EDITS_VERBATIM}` (the verbatim text of the edits the user picked).

## Final Output

Print to the user:
- Scene brief path
- Scene frame path
- Scene draft path
- Post-scene summary path
- Audit card path
- (If Stage 6 ran) brief note that fixes were applied
