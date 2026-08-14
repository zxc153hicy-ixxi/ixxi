# Table Mode

Write the Table blobs for an existing breakdown. You are given a numbered breakdown file and must produce only the Table-style blobs, preserving their original numbers.

## Voice & POV

Tables are structural, not narrative. No POV, no "you." Each cell is a self-contained reference entry — factual, evocative, and terse.

## Hard Rules

These are non-negotiable constraints. Violate none of them.

### Dimensions
1. Tables must use one of these exact configurations:

| Cells | Rows | Columns |
|-------|------|---------|
| 2     | 1    | 2       |
| 3     | 1    | 3       |
| 4     | 2    | 2       |
| 6     | 3    | 2       |
| 8     | 4    | 2       |
| 9     | 3    | 3       |
| 12    | 4    | 3       |

2. The breakdown header specifies the cell count: `## TABLE (4)` means a 4-cell table (2 rows × 2 columns).

### Word Limits
3. **Per cell**: 70 words maximum.
4. **Per table**: 200 words maximum total. This is a ceiling, not a target. A 90-word table is fine. A 140-word table is fine. Do not pad cells to approach 200.
5. **Vary cell lengths deliberately.** Within a single table, cells should differ noticeably in length. A table where every cell is 25-30 words is a failure state. Mix short punches (8-15 words) with longer entries (30-60 words). Let the content dictate length — some items need one sentence, others need three.
6. **Vary totals across tables.** Across multiple tables in a single run, the word counts should range widely. Not every table should cluster near 150-200 words. Some tables should be lean (60-100 words total), others fuller.

### Structure
7. **No column headers.** Data starts immediately.
8. Each cell follows the format: `**Title** Explanatory text.`
9. Bold title, one space, then description.

### Formatting
10. **Single-row tables** (2 or 3 cells): Compact format — separator row immediately follows content.
11. **Multi-row tables** (4+ cells): Expanded format — full separator line with dashes.

### Content
12. **Binary choices** (left/right, yes/no, take/leave) ALWAYS use a 2-cell table.

## What Table Blobs Cover

Table blobs present game-mechanic content the reader might screenshot or reference:
- **Items**: Loot, equipment, consumables, trinkets, cursed objects
- **Locations**: Rooms, hiding spots, landmarks, dungeon areas
- **Choices**: Binary decisions, branching paths, risk/reward forks
- **Traps**: Hazards, environmental dangers, trigger mechanisms
- **NPCs**: Character rosters, enemy types, ally catalogs
- **Quests**: Objectives, tasks, optional goals

If the content isn't something a player would consult like a reference card, it's not a Table blob.

## Tone

Concrete and evocative. Each cell should feel like a discoverable game object — something with weight, history, or consequence. Not clinical inventory text; not flowery prose. The sweet spot is atmospheric brevity.

Avoid:
- Generic descriptions ("a useful item", "a dangerous place")
- Mechanical stats without flavor ("deals 10 damage")
- Sentences that start with "This is" or "There is"
- Questions

## Workflow

1. **Read the full breakdown** to understand the scene arc and where Table blobs sit in the sequence.
2. **Identify each Table blob** in the breakdown — note the size in parentheses and the bullet points describing contents.
3. **Determine dimensions.** Use the cell count to find rows × columns from Hard Rule #1.
4. **Draft cells.** Write a bold title + description for each cell. Keep each under 70 words.
5. **Add header if needed.** Only if brief context is essential. Use `### Header Title` format above the table.
6. **Format correctly.** Single-row = compact. Multi-row = expanded.
7. **Validate.** Check every hard rule: correct cell count, word limits (per-cell and total), no column headers, proper formatting, bold titles.

## Output Format

```markdown
# [Scene Title] — Table Blobs

## 3. TABLE (3)

| **Title A** Description text. | **Title B** Description text. | **Title C** Description text. |
| --- | --- | --- |

## 7. TABLE (4)

### Optional Header

| **Title A** Description text. | **Title B** Description text. |
| ----------------------------- | ----------------------------- |
| **Title C** Description text. | **Title D** Description text. |

## 12. TABLE (2)

| **Title A** Description text. | **Title B** Description text. |
| --- | --- |
```

The output file should be named `[Scene-Title]-Table-Blobs.md`.

**CRITICAL:** Output ONLY Table blobs. Do not write blobs for any other style. Do not renumber — preserve the exact numbers from the input breakdown.

## Examples

### Example 1: 3-cell NPC table (single-row)

## 5. TABLE (3)

| **Man with Sheep's Wool** A coarse beard of curly white wool cover's half of this cursed man's face. | **The Broom Woman** She holds one. If you touch the fading handle, some of the flaking paint will slip into your skin. | **Time-Eyes** The paint of his eyes alone has fallen away, leaving two pupils like the hands of clocks. No matter how long you stare, the hands refuse to move. |
| --- | --- | --- |

### Example 2: 4-cell location table with header (multi-row)

## 8. TABLE (4)

### Places to Hide

| **Ald Medas Shrine** In this tall chamber of The Heather Vault, you crouch among the splintered piles of ten thousand exhausted magical wands. | **Big Eye's Cave** Seven ivory eggs encased in amber stud the ceiling.                                                                                                                 |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Selgon** This pillared corridor reminds you of an apprentice knight you once escorted through a similar sepulcher.                           | **Index Chamber** A snake of yellow light slithers constantly through the air between two pilons in this room. The shifting illumination makes this a surprisingly-good place to hide. |

### Example 3: 2-cell binary choice (single-row)

## 11. TABLE (2)

| **Right** The slope, in buckles and gnarls, rises gradually like a whole landscape of crags, of wooden hills and wooden cliffs. Branches, like trees in their own right, burst up from the rugged terrain like volcanic mushrooms. There is no easy path up the slope; the little 'branch trees' thicken into a thicket, the tunnels through the thicket shrink and shrink. | **Left** Your branch opens onto a wide, flat ledge. The light looks brighter this way. A place for your Blue Lady to catch her breath? |
| --- | --- |
