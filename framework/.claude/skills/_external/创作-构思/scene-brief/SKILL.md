---
name: scene-brief
description: Produce a single self-contained scene brief — exactly the context an LLM needs to draft the named scene as prose, and nothing else. Given a file containing the scene outline, plus optional set of supplementary context files, extracts only the material that will affect what gets written. Triggers include "scene brief", "brief the scene", "prep a scene".
---

# Scene Brief

Produce one self-contained briefing document for one scene. Goal: give a downstream LLM **exactly what it needs to draft the scene in prose, and absolutely nothing else.**

## Inputs

- `PRIMARY_PATH` — file containing the target scene outline (may also contain other material).
- `SCENE_TAG` — identifier for the target scene (e.g. `scene-4`, `dreamreel`). Often inferable from the user's phrasing: "write scene four of outline.md" → `scene-4`; "the dreamreel scene" → `dreamreel`. Confirm with the user only if genuinely ambiguous.
- `CONTEXT_PATHS` — optional, zero or more supplementary files (prior scene prose, world bible, character sheets, source style passages, etc.).

## Setup

1. Verify `PRIMARY_PATH` exists. Halt and report if missing.
2. If `CONTEXT_PATHS` were provided, verify each exists. Halt and report any missing.
3. Resolve `SCENE_TAG`. Infer from the user's prompt where possible; confirm with the user only if ambiguous.

## Method

Read `PRIMARY_PATH` and all `CONTEXT_PATHS`. Locate the scene matching `SCENE_TAG`.

Extract only what is *necessary* for the LLM to write that scene in prose **without referencing any other document**. Apply the **exclusion test** to every line of supplementary context you draft:

> *If I deleted this line, would the resulting scene prose be measurably worse?*

If no, delete it.

- *Necessary* example: a secret revealed in an earlier scene that affects character relationships in this one.
- *Unnecessary* example: a statement of belief from an earlier scene that doesn't affect this one.

## Output structure

Write the brief to `output/scene-brief-{SCENE_TAG}.md`.

### Required sections

- **`# Scene {SCENE_TAG} Brief`** — title.
- **`## Premise`** — one paragraph: POV, tense, target wordcount, and a brief, single-paragraph premise of the larger story, distilled from the source material.
- **`## Scene Outline`** — preserved from the source. You may paraphrase, summarize, or reorder only if the original material would confuse the LLM writing the prose. You may not add elements, unecessary justification, or further instructions to this outline.

### Optional sections

Include any of the following only if the source material contains relevant content AND that content will affect the writing of this scene. Name sections as you see fit; the list below is a starting menu, not a checklist. You may invent additional sections if the source demands them.

- **Already Rendered (DO NOT RE-DESCRIBE)** — character physical descriptions, setting features, sensory details, named props that have already been depicted in earlier scene prose. Critical when prior-scene prose is supplied.
- **Carry-Forward State** — physical positions of characters as this scene picks up, emotional states, in-progress conversations, active props or beats that persist.
- **Upstream Revelations** — secrets, plants, or revelations from earlier scenes that bear on this one.
- **Downstream Setups** — foreshadowing or planted detail this scene must seed for future scenes.
- **Ending Text (prior scene)** — final ~50 words of the prior scene, prefixed with `...` if needed.
- **Character voice / speech notes** — only if voice rules differ for this scene or aren't obvious from the outline.
- **Setting / sensory anchors** — only if the setting requires fixed details to hit.
- **Tonal or POV shift markers** — only if this scene differs in tone or POV from neighbors.

Every section must survive the exclusion test.

## Wordcount cap

Everything in the brief **except the scene outline** must fit in **20%** of the combined wordcount of all supplementary source material (including words from any material in `PRIMARY_PATH` not directly part of the scene), OR **400 words**, whichever is smaller.

The scene outline does not count toward the cap.

After writing, count the brief's words (excluding the main scene outline) with `wc -w` against an extracted copy. If over budget, prune lowest-impact lines (unecessary justification or rephrasing) and recheck.

## Final pass

Before declaring done, re-read each line of supplementary context you wrote. For each, ask: *if I deleted this line, would the resulting scene be measurably worse?* If not, delete it.

## Report

Print the absolute path of the brief written.
