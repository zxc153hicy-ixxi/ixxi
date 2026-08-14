# Breakdown Mode

Take a story idea, scene, or chapter concept and decompose it into an ordered sequence of typed blobs.

**You are NOT writing prose.** You are creating a structural outline — a sequence of labeled blob headers, each with a short list of bullet points describing what that blob covers.

## What Is a Blob?

A blob is a short text block in one of five styles: Verse, Essay, Interview, Memorials, or Lemma. In Breakdown mode, each blob is represented as:

```
## N. STYLE
- bullet point (5-15 words)
- bullet point
- ...
```

Each blob gets 3-10 bullet points. Bullets are terse — just enough to capture intent, not full sentences.

### Blob Style Quick Guide

Use this to decide which style fits each story beat:

- **VERSE** — Physical action recounted after-the-fact by the necromancer: combat, casting, traversal, a sudden event. Scholarly-archaic prose split into stacked text-message clauses. Use when the reader needs to feel a beat of physical action unfolding.
- **ESSAY** — The workhorse non-action blob. First-person discursive reasoning: exposition, reflection, speculation, argument about a setting element, creature, phenomenon, or memory. Hedges, digresses, addresses the reader as "you."
- **INTERVIEW** — A single named NPC speaks, prompted by brief bolded question fragments. The main character (the protagonist necromancer) is **always** the interviewer — the bolded prompts are their abbreviated questions, never spoken aloud by any other party. The main character never answers and is never the interviewee. Use when an NPC has an agenda, confession, tirade, or revelation to deliver in their own voice. If a beat requires the protagonist to speak at length, use Essay instead.
- **MEMORIALS** — A sequence of 2-4 epitaphs in the register of carved stone: formal, aphoristic, compressed. Either honors the dead or addresses passing readers. Use at thresholds, deaths, arrivals, and wherever compressed wisdom-in-stone fits.
- **LEMMA** — A single encyclopedia entry on a specific entity: monster, location, spell, item, disease, plant, curse. Third-person omniscient reference prose. Use as punctuation to anchor canonical info about something the reader has just encountered.

## Sequencing Rules

These are hard constraints. Do not violate them.

### Minimum diversity
- At least **4 of the 5** blob styles must appear in any scene.

### Adjacency limits (how many of the same style in a row)
| Style     | Max consecutive | Additional caps                                          |
| --------- | --------------- | -------------------------------------------------------- |
| Verse     | 3               | May NOT be the first blob                                |
| Essay     | 2               | —                                                        |
| Interview | 2               | —                                                        |
| Memorials | 1               | Max 3 total per scene                                    |
| Lemma     | 1               | Max 3 total per scene; May NOT be the first or last blob |

### General pacing guidance
- **Open with** Essay or Memorials — ground the reader before any action.
- **Close with** Verse, Essay, or Memorials — never Interview or Lemma.
- Alternate styles frequently. Long runs of one style feel monotonous.
- Use Lemmas as punctuation — they anchor a specific canonical element after the reader meets it.
- Interview blobs are breathers. Place them after intense Verse stretches or heavy Essay sections.
- Consecutive Verse blobs should read as escalating phases of a single event (phase-1 → phase-2 → resolution).
- Blob count is dictated by the scene. No fixed target, but minimum 4 (to satisfy the diversity rule).

## Workflow

1. **Read the scene idea.** Understand the arc: what is the setup, the core tension, and the resolution (or cliffhanger)?
2. **Identify the major beats.** What events, reveals, choices, encounters, and transitions need to happen?
3. **Assign a blob style to each beat.** Use the Quick Guide above. Some beats naturally combine (an Essay mapping the chrypt's layout followed by a Verse as the ward-trap snaps shut, for instance).
4. **Check constraints.** Walk the sequence and verify every rule in the Sequencing Rules section. Fix violations before presenting.
5. **Copy template and fill.** Copy `assets/Breakdown-Template.md` to working directory as `[Scene-Title]-Breakdown.md`. Replace the example content with the new breakdown. Follow the output format below.

## Output Format

Every blob header is numbered sequentially. This numbering is critical — it enables style modes to be written independently and merged later by number.

```markdown
# [Scene/Chapter Title]

## 1. ESSAY
- bullet
- bullet
- ...

## 2. MEMORIALS (4)
- bullet previewing epitaph 1
- bullet previewing epitaph 2
- bullet previewing epitaph 3
- bullet previewing epitaph 4

## 3. VERSE
- bullet
- bullet
- ...

## 4. INTERVIEW (3) — [NPC Name — never the main character], [optional circumstance]
- bullet (Q/A exchange 1)
- bullet (Q/A exchange 2)
- bullet (Q/A exchange 3)

## 5. LEMMA — [Entity Name]
- bullet describing what the entry covers
- bullet
- ...
```

### Notes on format
- Memorials note the epitaph count in the header (2, 3, or 4). Vary the counts between blobs (not all 3 for example). Bullets preview each epitaph (one bullet per epitaph).
- Interview headers include the exchange count, the NPC's name, and an optional circumstance. Vary the counts between blobs (not all 3 for example). Each bullet represents one Q/A exchange (2-4 per blob). **The named character must be an NPC. The main character / protagonist necromancer is always the interviewer and is never named in the header.** If a beat requires the protagonist to speak at length (confess, persuade, lie, monologue), use Essay instead.
- Lemma headers name the specific entity catalogued.
- Verse and Essay follow the generic 3-7 bullets convention.
- Keep bullets to 5-15 words.

## Example

See `assets/Breakdown-Template.md` for a complete example breakdown of a sunken-tohmb soul-diving rite (The Liminal Diver).
