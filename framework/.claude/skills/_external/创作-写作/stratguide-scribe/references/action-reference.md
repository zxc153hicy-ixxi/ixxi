# Action Mode

Write the Action blobs for an existing breakdown. You are given a numbered breakdown file and must produce only the Action-style blobs, preserving their original numbers.

## Voice & POV

Second person throughout. You are writing a strategy guide — the reader is the player. Address them with "you" and "your."

## Hard Rules

These are non-negotiable constraints. Violate none of them.

### Structure
1. Each Action blob is a **single paragraph**. No line breaks, no bullet points, no sub-sections.
2. Each Action blob is wrapped in **backticks** (inline code style): `` `Your only hope is...` ``
3. Each blob is **40–150 words**. Never under 40, never over 150.
4. No more than **6 sentences** per blob.

### Length Variety
When writing multiple Action blobs for the same scene, **vary word counts significantly**. If there are 3 Action blobs, don't make them all ~100 words. One might be 50, the other two 120–140. Monotonous blob lengths make the scene feel mechanical.

### Content
5. **No interiority.** Never describe the reader's thoughts, feelings, emotions, or internal state. Only external actions, observations, and consequences.
6. **No naming the main character.** The reader is "you" — never give them a name, title, or epithet.
7. At least **3 imperative verbs** per blob. Command the reader: retreat, pull, duck, follow, strike, avoid, cross, etc.
8. At least **1 conditional/branching statement** per blob. Present an if/then, an alternative, or a consequence fork ("if you X, then Y; otherwise Z"). This creates the illusion of choice.
9. No more than **2 sentences** may pass without directing the reader to do something (an imperative, a conditional, or a warning about consequences of action/inaction).

### Consecutive Action Blobs
10. When 2–3 Action blobs appear consecutively in the breakdown, treat them as **escalating phases** of a single challenge (e.g., boss phase 1 → phase 2 → phase 3, or chase stage 1 → stage 2 → escape). Each phase should raise the stakes or change the conditions.

## What Action Blobs Cover

Action blobs are for moments where the reader must *do* something:
- **Combat**: Boss fights, ambushes, duels, monster encounters
- **Traversal**: Navigation, chases, escape sequences, climbing, crossing hazards
- **Puzzles**: Environmental puzzles, lock mechanisms, ritual steps
- **Choices**: Branching paths, risk/reward tradeoffs, timed decisions

If a beat in the breakdown doesn't involve the reader physically doing something, it's not an Action blob — the breakdown should not have tagged it as one.

## Tone

Direct, confident, slightly conspiratorial — like a guide writer who has played this section dozens of times and is giving you the optimal route. Not clinical; there's personality. The guide writer notices the world (a specific environmental detail, a creature's behavior, an odd architectural feature) but always in service of telling you what to *do* about it.

Avoid:
- Flowery language or extended metaphor
- Exclamation marks
- Questions directed at the reader (use imperatives instead)
- Meta-commentary ("this is a tough fight", "this part is tricky")

## Workflow

1. **Read the full breakdown** to understand the scene arc and where Action blobs sit in the sequence.
2. **Read the action-reference.md** (this file).
3. **For each Action blob in the breakdown**, write the blob text using the bullet points as your content guide. The bullets tell you *what* happens; you decide *how* to phrase it as guidebook prose.
4. **Verify every hard rule** (word count, sentence count, imperatives, conditionals, no interiority, backtick wrapping).
5. **Output only the Action blobs**, each under its original numbered header.

## Output Format

```markdown
# [Scene Title] — Action Blobs

## 4. ACTION

`Your blob text here, single paragraph, 40-150 words, wrapped in backticks.`

## 7. ACTION

`Another action blob, preserving the original number from the breakdown.`
```

The output file should be named `[Scene-Title]-Action-Blobs.md`.

**CRITICAL:** Output ONLY Action blobs. Do not write blobs for any other style. Do not renumber — preserve the exact numbers from the input breakdown.

## Example

Given breakdown blob:

```
## 4. ACTION
- Stay in starting area when fight begins
- Let Dreadlord come to you
- Moving deeper into the room aggros hidden portrait wraiths
- If you do aggro them, use a divine weapon to permanently kill the wraiths
- No divine weapon? Just dodge until Dreadlord arrives
```

Written output:

## 4. ACTION

`Hold your ground at the nave entrance when the Dreadlord stirs — do not advance toward the altar. Let the thing come to you. Moving deeper into the chapel will aggro the portrait wraiths still clinging to the shattered frames along the north wall. If you do pull them, switch to a divine weapon and cut them down before the Dreadlord closes the distance; wraiths killed with consecrated steel stay dead. If you have no divine weapon, keep dodging laterally between the overturned pews until the Dreadlord arrives and the wraiths lose interest.`
