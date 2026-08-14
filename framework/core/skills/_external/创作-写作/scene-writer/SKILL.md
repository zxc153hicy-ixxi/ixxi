---
name: scene-writer
description: Write a complete prose scene from a given scene outline. Use when asked to "write a scene", "draft a scene", "write the next scene", or any request to produce narrative prose from story context.
---

# Scene Writer

You are the orchestrator. Spawn four sequential `general-purpose` phase agents (`model: sonnet`), each writing one section of the scene. The agents share state through a single working document that lives on disk and gets edited in place.

You do NOT write any prose yourself. Your jobs are: launching agents in order, reading the working doc between phases for sanity, and assembling the final scene file at the end.

## Inputs

The user (or a calling skill) provides one or more files giving the scene's context — at minimum a scene outline; commonly a scene brief and a scene frame. Collect every input file path as `INPUT_PATHS`. Identify or ask for:

- `STORYNAME` — short story label (used in filenames and the scene title)
- `SCENE_NUM` — scene number or label
- `WORDCOUNT` — target total wordcount for the finished scene

## Working files

- `WORKING_DOC` = `output/working-doc-{STORYNAME}-Scene-{SCENE_NUM}.md` — created by Agent 1, edited in place by Agents 2–4, deleted at the end.
- `SCENE_FILE` = `output/{STORYNAME}-Scene-{SCENE_NUM}.md` — the final scene file.

## Workflow

Run agents sequentially. If any agent fails or its expected output is missing, halt and report.

Each agent must read its phase reference (`references/<phase>.md`) LAST — reading it counts as beginning the phase.

### Agent 1 — Pre-Setup

Spawn a `general-purpose` subagent (`model: sonnet`) with this prompt:

> You are Agent 1 of 4 running the `scene-writer` skill. Your job is pre-setup only — Steps 1–2 of the skill. Do NOT write scene prose.
>
> Read in order:
> 1. Each context file in `{INPUT_PATHS}`.
> 2. `.claude/skills/scene-writer/references/pre-setup.md` (last — reading it begins the phase).
>
> Address all six pre-setup tasks. Decide establishing vs. continuation.
>
> Condense to under 300 words total and write to `{WORKING_DOC}` using the template at `.claude/skills/scene-writer/assets/working-doc.md`. Storyname: `{STORYNAME}`. Scene: `{SCENE_NUM}`. Leave the `### Setup`/`### Conflict`/`### Resolution` placeholders under `## Draft` untouched.
>
> Target wordcount for the full scene: `{WORDCOUNT}` words.
>
> Report under 120 words: working doc path, final word count (`wc -w`), any judgment calls. Do NOT paste the working doc back.

### Agent 2 — Setup

Spawn a `general-purpose` subagent (`model: sonnet`) with this prompt:

> You are Agent 2 of 4 running the `scene-writer` skill. Your job is the SETUP phase only — Steps 3–4 of the skill.
>
> Read in order:
> 1. Each context file in `{INPUT_PATHS}` (treat every section as binding).
> 2. `{WORKING_DOC}` — Agent 1 already wrote the Pre-Scene Work; the Draft section's placeholders are empty.
> 3. `.claude/skills/scene-writer/references/setup.md` (last — reading it begins the phase).
>
> Write the setup prose. Total scene target: `{WORDCOUNT}` words. Setup is 5–15% of that for continuation scenes, 25–30% for establishing.
>
> Replace the `[Append setup prose here after Step 3]` placeholder in `{WORKING_DOC}` with your prose. Delete every texture you spent from the inventory and renumber.
>
> Follow every per-character speech rule and forbidden-pattern in the scene frame, if one is provided.
>
> Report under 120 words: setup word count, textures spent (by current #), one judgment call. Do NOT paste prose back.

### Agent 3 — Conflict

Spawn a `general-purpose` subagent (`model: sonnet`) with this prompt:

> You are Agent 3 of 4 running the `scene-writer` skill. Your job is the CONFLICT phase only — Steps 5–6.
>
> Read in order:
> 1. Each context file in `{INPUT_PATHS}`.
> 2. `{WORKING_DOC}` — Setup is already drafted; you continue from where it ends.
> 3. `.claude/skills/scene-writer/references/conflict.md` (last).
>
> Write the conflict prose. Total scene target: `{WORDCOUNT}` words. Conflict is 50–60% of that; hard cap 70%.
>
> Leave 1–2 textures in the inventory for the resolution agent. If the brief specifies a closing image or beat, reserve the texture(s) supporting it.
>
> Replace the `[Append conflict prose here after Step 5]` placeholder with your prose. Delete every texture you spent and renumber.
>
> Follow every per-character speech rule and forbidden-pattern in the scene frame, if one is provided.
>
> Report under 120 words: conflict word count, textures spent (by current #), textures reserved, one judgment call. Do NOT paste prose back.

### Agent 4 — Resolution

Spawn a `general-purpose` subagent (`model: sonnet`) with this prompt:

> You are Agent 4 of 4 running the `scene-writer` skill. Your job is the RESOLUTION phase only — Steps 7–8.
>
> Read in order:
> 1. Each context file in `{INPUT_PATHS}`.
> 2. `{WORKING_DOC}` — Setup and Conflict are drafted; you continue from where Conflict ends.
> 3. `.claude/skills/scene-writer/references/resolution.md` (last).
>
> Write the resolution prose. Total scene target: `{WORDCOUNT}` words. Resolution is 10–20% of that.
>
> Spend ALL remaining textures from the inventory; the inventory must be empty after.
>
> Replace the `[Append resolution prose here after Step 7]` placeholder with your prose. Empty the texture inventory.
>
> Follow every per-character speech rule and forbidden-pattern in the scene frame, if one is provided.
>
> Report under 100 words: resolution word count, how the closing texture(s) were staged, one judgment call. Do NOT paste prose back.

### Final Assembly

Read `{WORKING_DOC}`. Create `{SCENE_FILE}` from `assets/scene-template.md`:
- Substitute the title: `# {STORYNAME}: Scene {SCENE_NUM}`.
- Combine the Setup, Conflict, and Resolution sections into continuous prose. **Remove the phase subheaders** (Setup / Conflict / Resolution) so the prose reads as a single unbroken scene.

Delete `{WORKING_DOC}`.

Report `{SCENE_FILE}` to the user. Suggest running `scene-review` next if they want to revise and produce a post-scene summary.

## File Structure

```
scene-writer/
├── SKILL.md
├── references/
│   ├── pre-setup.md      # creative guidance for Agent 1
│   ├── setup.md          # creative guidance for Agent 2
│   ├── conflict.md       # creative guidance for Agent 3
│   └── resolution.md     # creative guidance for Agent 4
└── assets/
    ├── working-doc.md    # template Agent 1 instantiates
    └── scene-template.md # template the orchestrator instantiates
```
