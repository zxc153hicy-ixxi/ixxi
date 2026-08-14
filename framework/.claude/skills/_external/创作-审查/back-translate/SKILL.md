---
name: back-translate
description: Run a scene or passage through a foreign language and back into English ("telephone"), keeping the foreign accent instead of smoothing it out, to surface defamiliarized prose. One subagent translates the source into a target language leaning into that language's distinct features; a second, isolated subagent translates it back to English preserving those features. Triggers include "back-translate", "language telephone", "round-trip translate", "run this through [language] and back".
---

# Back-Translate

Run a passage through a foreign language and back to English to surface fresh, slightly alien prose — the telephone game applied to fiction. The point is **distortion**, not fidelity: the round trip drags in another language's grain (Germanic compounds, Japanese evidentiality and dropped subjects, Russian aspect, French abstraction) and leaves an English text with a foreign accent.

You are the **orchestrator**. You do not translate anything yourself. You resolve inputs, launch two subagents in sequence, and report.

## Inputs

- `SOURCE_PATH` — file containing the text to run through the round trip.
- `LANGUAGE` — the target language for the round trip (e.g. German, Japanese, Russian).

Infer both from the user's phrasing where possible ("run Test-Scene through German and back" → `SOURCE_PATH=input/Test-Scene.md`, `LANGUAGE=German`). Confirm only if genuinely ambiguous.

## Setup

1. Resolve `SOURCE_PATH` to an absolute path. Verify it exists. Halt and report if missing.
2. Resolve `LANGUAGE`.
3. Derive the output path: `output/{SourceBasename}-{LANGUAGE}-Flavor.md`, where `SourceBasename` is the source filename without extension (e.g. `output/Test-Scene-German-Flavor.md`). Use an absolute path when passing it to subagents.

## Method

Launch two subagents **in sequence** using the Agent tool. The second depends on the first finishing.

**Isolation is the whole trick.** Each subagent must read *only* the one file it is told to read. If the back-translator sees the original English, the distortion collapses and the exercise is pointless. Enforce "Do not read any other files" in both prompts.

Pass **absolute paths** in every prompt. Use an opus-level subagent for both (`subagent_type: general-purpose`, `model: opus`).

### Subagent 1 — into the target language

Prompt (substitute the resolved values):

```
Hey claude, read {ABSOLUTE_SOURCE_PATH}. Do not read any other files. I want you to
translate all the text in this file into {LANGUAGE}. Focus on weaving in some of the
peculiarities, or distinct features, of {LANGUAGE}, which set it apart from the original
English. Write your results to {ABSOLUTE_OUTPUT_PATH}.
```

Wait for it to finish before launching the next.

### Subagent 2 — back into English (isolated)

Prompt (substitute the resolved values):

```
Hey claude, read {ABSOLUTE_OUTPUT_PATH}. Do not read any other files. I want you to
translate all the text in this file into *English*. Focus on keeping/capturing the
peculiarities, or distinct features, of the original {LANGUAGE}, which set it apart from
English. Write your results to the existing {ABSOLUTE_OUTPUT_PATH} (overwrite the current
text).
```

The final file at the output path holds the back-translated English (accented by `{LANGUAGE}`), overwriting the intermediate foreign text.

## Report

Print the absolute path of the final output file. Note in one line which language the text was run through.
