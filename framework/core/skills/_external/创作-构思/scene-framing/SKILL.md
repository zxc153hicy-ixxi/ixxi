---
name: scene-framing
description: Produces a single scene-frame document with any combination of four card types (scene parameters, source imprint, speech rules, forbidden patterns) before drafting. Triggers include "scene framing", "scene frame", "frame the scene", "produce cards", and any request mentioning the individual card types ("give me a blacklist", "speech card", "imprint", "scene parameters").
---

# Scene Framing

Produces a single markdown document with any combination of four card types.

## Inputs (all optional)

- **Scene context** — a working-context file or scene outline. Used by `params`, `speech`, and `blacklist` (PREDICTIVE mode).
- **Source passage** — 1-3 paragraphs of source prose. Used by `imprint`. May also override rolls in `speech` if speech samples are present.
- **Character info** — name, brief description, or profile per speaking character. Used by `speech`.
- **Scene tag** — short identifier for the output filename (e.g. `scene-2`, `dreamreel-s2`).

If `scene tag` is not provided, derive a short tag from the scene context filename. If you cannot, ask the user.

## Card selection

The user request determines which cards to produce. Recognized names:

- `params` — scene parameters
- `imprint` — source imprint
- `speech` — speech rules (one card per speaking character; user may specify which)
- `blacklist` — forbidden patterns

**Default:** if the user does not specify, produce **all four**.

**Skip rules:**
- Skip `imprint` if no source passage is provided.
- Skip `speech` if no speaking characters can be identified from the scene context or user request.
- Skip `params` and `blacklist` if no scene context is provided AND the user did not explicitly request them.

If the user requests a card whose required input is missing, halt and report what's missing.

## Producing each card

Use `assets/sampling.py` for rolls. All vocabulary lives in `assets/vocabulary.json`.

### params (scene parameters)

Note any user-locked axes (e.g., "POV must be close") and skip the roll for those.

For each unlocked axis:
```
python assets/sampling.py senses 3
python assets/sampling.py rhythms 2
python assets/sampling.py scene_shapes 1
python assets/sampling.py color_palettes 1
```

One short rationale sentence per axis tying the choice to the scene. Under 100 words.

### imprint (source imprint)

Read source paragraphs. Extract style features by direct observation, not by author or genre label. Extract 4-7 concrete features, at minimum:

- Sentence-length distribution (e.g., "alternates 4-7 word and 25-40 word sentences; no middle range")
- Clause stacking (left-branching, right-branching, parenthetical, periodic)
- Register and vocabulary (archaic, plain, Latinate, colloquial; contractions y/n)
- Dominant sensory channels
- Signature tics (recurring conjunctions, punctuation habits, repetition patterns)

Derive a short **do this / don't do this** rule list. Under 100 words.

### speech (speech rules — one per character)

For each speaking character:
```
python assets/sampling.py positive_modes 2
python assets/sampling.py vocab_registers 2
python assets/sampling.py sentence_length_caps 2
python assets/sampling.py signature_constructions 2
```

After rolling, select 1 of the two rolled values per axis; the most-fitting given the character/scene context.

If source paragraphs of the character's speech are provided, override rolled choices that conflict with concrete features extracted directly from the source.

Apply **default-banned patterns** as constants (always banned, never rolled):
- "What does it feel like" type questions
- Fragment-as-style (unless the rolled positive mode requires it)

**Saturation cap** (constant): signature construction and positive mode each fire on no more than ~50% of the character's lines.

Each character card includes: positive mode, register, sentence-length cap, signature construction, default-banned patterns. Under 60 words per character.

### blacklist (forbidden patterns)

```
python assets/sampling.py simile_bans 2
python assets/sampling.py cadence_bans 2
python assets/sampling.py syntactic_bans 1
python assets/sampling.py imagery_bans 2
python assets/sampling.py register_bans 1
```

Use rolled rules verbatim. If the user supplies additional bans, append them.

If `PREDICTIVE` mode is specified, add a section **Scene-specific Bans:** with 2-4 bullets based on the scene context.

Under 100 words.

## Output

Write a single file: `output/scene-frame-[scene-tag].md`.

Structure:

```markdown
# Scene Frame — [scene-tag]

## Scene Parameters
<params card body>

## Source Imprint
<imprint card body>

## Speech Rules

### [Character Name 1]
<speech card body>

### [Character Name 2]
<speech card body>

## Forbidden Patterns
<blacklist card body>
```

Include only the sections corresponding to cards actually produced. Omit headers for skipped cards.

Do not add categories beyond what each card spec defines. Do not exceed the per-card word caps.
