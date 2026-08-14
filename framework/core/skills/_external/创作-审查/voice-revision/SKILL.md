---
name: voice-revision
description: Revise, rewrite, or redo prose in specific character 'voices'. Use when user asks to revise text in Freeman, Paladin, Thorogood, Rogue, or Necromancer voice. Also use for any request to rewrite with a particular voice or as a particular character.
---

# Literary Revision

Revise user-provided prose into a specific character voice while preserving core narrative beats.

## Workflow

1. Identify requested voice from user input
2. Load the appropriate voice reference from `references/`:
   - **Static voices** (Freeman, Paladin, Thorogood, Rogue): read the reference file directly.
   - **Generated voices** (Necromancer): run the generator first, then read its freshly-built reference. See "Generated Voices" below.
3. Extract core beats from source prose (outline, not rewrite)
4. Apply guidelines systematically
5. Verify output respects any character limit specified

## Generated Voices

**Necromancer:** before reading the reference, regenerate it:

```
python .claude/skills/voice-revision/assets/build_voice.py
```

This writes `references/necromancer-voice.md` (overwriting any prior run). Then read that file.

## Available Voices

| Voice         | Voice                                    | Use Case                                      | Reference            |
| ------------- | ---------------------------------------- | --------------------------------------------- | -------------------- |
| **Freeman**   | Neurotic 1st person, stream of consciousness | Comedic self-interested survival narration | [freeman-voice.md]   |
| **Paladin** | Devout questing knight, radiant faith inner monologue | Earnest pilgrim narration with wondering diction | [paladin-voice.md] |
| **Thorogood** | Bar-band storyteller, 2nd person, bluesy | Punchy, rhythmic retellings with attitude | [thorogood-voice.md] |
| **Rogue** | Grandiloquent confidence man, elevated diction | Formal rhetoric as weapon, every conversation a negotiation | [rogue-voice.md] |
| **Necromancer** | Archaic scholarly necromancer (Othelmedir), grimoire cadence | Latinate horror narration at one remove, cold authority | *generated* → necromancer-voice.md |

## Voice Selection

- User says "Freeman," "Freeman's Mind," "neurotic," "inner monologue," "stream of consciousness" → Load freeman-voice.md
- User says "Paladin," "radiant faith," "questing knight" → Load paladin-voice.md
- User says "Thorogood," "bluesy," "bar story," "roadhouse" → Load thorogood-voice.md
- User says "Rogue," "grandiloquent," "confidence man," "con man," "formal rhetoric" → Load rogue-voice.md
- User says "Necromancer," "Othelmedir," "grimoire," "Time of Dying," "archaic necromancer" → Run the generator (see "Generated Voices"), then load necromancer-voice.md
- Ambiguous request → Ask user to specify voice

## Output Guidelines

- Preserve all core narrative beats from source
- Respect character limits if specified (default: no limit)
- Do not add plot elements absent from source
- Voice transformation only—not content invention
