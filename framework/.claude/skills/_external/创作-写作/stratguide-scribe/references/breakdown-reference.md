# Breakdown Mode

Take a story idea, scene, or chapter concept and decompose it into an ordered sequence of typed blobs.

**You are NOT writing prose.** You are creating a structural outline — a sequence of labeled blob headers, each with a short list of bullet points describing what that blob covers.

## What Is a Blob?

A blob is a short text block (under 150 words when eventually written) in one of five styles: Action, Narrator, Description, Dialogue, or Table. In Breakdown mode, each blob is represented as:

```
## N. STYLE
- bullet point (5-15 words)
- bullet point
- ...
```

Each blob gets 3–7 bullet points. Bullets are terse — just enough to capture intent, not full sentences.

### Blob Style Quick Guide

Use this to decide which style fits each story beat:

- **ACTION** — The reader must *do* something: fight, choose, navigate, solve, avoid. Written like a strategy guide walkthrough. Often presents branching options ("if you X, then Y; otherwise Z").
- **NARRATOR** — A character (god, antagonist, ally, weapon, ghost, etc.) speaks directly to the reader. Narrator bullets describe what the narrator *does as a speaker*: warns, taunts, reveals, demands, offers, judges, foreshadows. **Narrator is NOT atmosphere or world-state rephrased as lore.**
- **DESCRIPTION** — The most versatile style. Regular second-person fiction prose covering environments, character/creature appearances, exposition-through-observation, transitions between locations or time, and aftermath. What the reader sees, hears, smells, and physically experiences — but never instructions (Action), narrator speech (Narrator), or NPC dialogue (Dialogue). The workhorse blob, but should not dominate a scene.
- **DIALOGUE** — A single named NPC speaks directly. Exactly four lines of quoted speech. Note the speaker in the header: `## DIALOGUE — [Character Name]`. The main character ("you") NEVER speaks. The NPC must have an agenda — quest-giving, antagonism, revelation, expressing emotion — not just flavor. Dialogue's unique strength: showing how "you" affects the world and the people in it.
- **TABLE** — Structured game-mechanic content: item lists, location indexes, binary choices, trap catalogs, quest options. Specify size in header: `## TABLE (N)` where N is 2, 3, 4, 9, or 12. Each entry is a bold title + short description.

## Sequencing Rules

These are hard constraints. Do not violate them.

### Minimum diversity
- At least **4 of the 5** blob styles must appear in any scene.

### Adjacency limits (how many of the same style in a row)
| Style       | Max consecutive | Additional caps                                          |
| ----------- | --------------- | -------------------------------------------------------- |
| Action      | 3               | May NOT be the first or last blob                        |
| Narrator    | 2               | Max 5 total per scene                                    |
| Description | 2               | —                                                        |
| Dialogue    | 1               | —                                                        |
| Table       | 1               | Max 3 total per scene; May NOT be the first or last blob |

### General pacing guidance
- **Open with** Description or Narrator — ground the reader before anything else.
- **Close with** Description, Narrator, or Dialogue — never Action or Table.
- Alternate styles frequently. Long runs of a single style feel monotonous.
- Use Tables as punctuation — they break up prose sections and give the reader something concrete to inspect.
- Dialogue blobs are breathers. Place them after intense Action or heavy Narrator stretches.
- Blob count is dictated by the scene. There is no fixed target, but the minimum is 4 (to satisfy the diversity rule).

## Workflow

1. **Read the scene idea.** Understand the arc: what is the setup, the core tension, and the resolution (or cliffhanger)?
2. **Identify the major beats.** What events, reveals, choices, encounters, and transitions need to happen?
3. **Assign a blob style to each beat.** Use the Quick Guide above. Some beats naturally combine (a Description followed by an Action for a trap, for instance).
4. **Check constraints.** Walk the sequence and verify every rule in the Sequencing Rules section. Fix violations before presenting.
5. **Copy template and fill.** Copy `assets/Breakdown-Template.md` to working directory as `[Scene-Title]-Breakdown.md`. Replace the example content with the new breakdown. Follow the output format below.

## Output Format

Every blob header is numbered sequentially. This numbering is critical — it enables style modes to be written independently and merged later by number.

```markdown
# [Scene/Chapter Title]

## 1. DESCRIPTION
- bullet
- bullet
- ...

## 2. NARRATOR
- bullet
- bullet
- ...

## 3. ACTION
- bullet
- bullet
- ...

## 4. DIALOGUE — [Character Name]
- bullet (line 1 of 4)
- bullet (line 2 of 4)
- bullet (line 3 of 4)
- bullet (line 4 of 4)

## 5. TABLE (4)
- bullet describing table theme/contents
- bullet
- ...
```

### Notes on format
- Dialogue blobs always have exactly 4 bullets (preview the 4 lines, do not write them).
- Table blobs note the size in parentheses and describe what the table contains, not the individual entries.
- All other blobs have 3–7 bullets.
- Keep bullets to 5–15 words. No full sentences, no prose.

## Example

See `assets/Breakdown-Template.md` for a complete example breakdown of a cursed chapel / Dreadlord encounter scene.
