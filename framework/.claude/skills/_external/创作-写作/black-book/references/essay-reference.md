# Essay Mode

Write Essay blobs for an existing breakdown. You receive a numbered breakdown and must produce only the Essay-style blobs, preserving original numbers.

This skill runs in two stages. **Do not skip stage 1.**

## Stage 1: Load the Voice

Before anything else:

1. Run `.claude/skills/black-book/assets/build_voice.py` (regenerates the voice file with a fresh randomized vocabulary draw). Use the `python` command, not `python3`.
2. Read and fully internalize `.claude/skills/black-book/assets/Voice.md`. This is your Voice & POV reference for diction, cadence, signature sentence patterns, vocabulary, rhetorical tactics, and forbidden tics.

Only proceed to Stage 2 after Voice.md has been read this session.

## Stage 2: Write the Essay Blobs

## Hard Rules

### Structure
1. Each blob is **2–4 paragraphs**. Paragraph breaks mark argumentative turns — claim, counterpoint, hedge, settle.
2. **No formatting.** No backticks, no italics, no bold, no bullet points, no headers within the blob. Plain prose only.
3. Each blob is **80–200 words**. Prefer variety over consistency.
4. No more than **14 sentences** per blob.

### Length Variety
When writing multiple Essay blobs for one scene, vary word counts significantly. An 85-word aftermath blob and a 190-word speculative blob can coexist in the same scene. Monotonous lengths flatten the rhythm.

### Content
5. **First person mandatory.** The essayist is always "I." Slide into "we" when invoking shared stakes. Never drift into third-person omniscient.
6. **At least one hedge or uncertainty marker per blob.** "I think," "perhaps," "I suspect," "it may be that," "methinks," "howbeit." Measured uncertainty is the defining move of essay voice.
7. **At least one concession, counterpoint, or digression per blob.** The writer concedes a counter-position, notes an aside, or lets the mind wander before returning. Thinking in public, not pronouncing.
8. **At least one concrete setting anchor per blob.** A named place, creature, spell, artifact, rite, or sensation. Abstract reasoning without grounding is not Essay.
9. **No dialogue.** No quoted speech. Attribution of prior claims to an unnamed source is fine ("some say," "past divers reported"), but no direct quotes.
10. **No in-the-moment physical action.** Essays may recall or speculate about action, but sequences of event-beats belong in Verse.
11. **Blobs stand alone.** Do not reference other numbered blobs in the scene ("as the verse below shows," "you have just read"). Each Essay is a self-contained entry.

## Tone

Thinking, not telling. The necromancer reasons openly, hedges, concedes, digresses, and settles on tentative conclusions. Rhythm alternates long Latinate constructions with shorter declarative beats.

Avoid:
- Exclamation marks
- Purple stacked adjectives ("the dark, brooding, ominous pool")
- Rhetorical triumphalism or clean conclusions
- Modern slang, contractions, post-1900 clinical jargon
- Pure description without reasoning attached — that borders Lemma

## Workflow

1. Confirm Stage 1 is complete: `build_voice.py` has been run and `Voice.md` has been read this session.
2. Read the full breakdown to understand the scene arc.
3. For each Essay blob, use the breakdown bullets as a content guide. The bullets say *what* to argue or reflect on; you decide *how* to render it as prose.
4. Decide paragraph count (2–4) based on the number of argumentative turns. A single reflection may take two; a hedged speculation with counterpoint may need four.
5. Verify every hard rule: word count, sentence count, first-person voice, hedge marker, concession/digression, setting anchor, no dialogue, no action beats, no cross-blob reference.
6. Output only the Essay blobs under their original numbered headers.

## Output Format

```markdown
# [Scene Title] — Essay Blobs

## 2. ESSAY

Your blob text here, 2-4 paragraphs, plain prose, 80-200 words.

## 6. ESSAY

Another essay blob, preserving the original number.
```

Name the output file `[Scene-Title]-Essay-Blobs.md`.

**CRITICAL:** Output ONLY Essay blobs. Do not write other blob types. Do not renumber.