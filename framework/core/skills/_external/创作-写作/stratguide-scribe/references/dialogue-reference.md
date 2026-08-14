# Dialogue Mode

Write Dialogue blobs for an existing breakdown. You receive a numbered breakdown and must produce only the Dialogue-style blobs, preserving original numbers.

## Voice & POV

Third person. A single named NPC speaks — the main character ("you") **never** speaks and is never quoted. The NPC addresses the reader directly when appropriate, but the dialogue belongs entirely to the NPC.

## Hard Rules

### Structure
1. Each blob is **exactly 4 lines**. No more, no fewer.
2. Each line is a blockquote with quoted speech: `> "Line text here."`
3. Each line is **1–30 words**.
4. **Total blob word count: 15–90 words.**

### Length Variety
5. **Not more than 2 of 4 lines may fall within a 5-word range of each other.** If lines 1, 2, and 3 are all 18–22 words, the blob is too uniform. Mix long and short — a 28-word line next to a 4-word line is good. One-word lines are legal and powerful.

### Content
6. **The main character never speaks.** No quoted speech from "you." The NPC is the only voice.
7. **No stage directions or narration.** The blob is pure speech — no action beats, no "he said," no descriptions of the speaker's body language between lines. The four lines are *only* what the NPC says aloud.
8. **Max 2 of 4 lines may contain "you" or "your."** NPCs prefer to talk about themselves (I, me, my), the subject at hand, or the world. Direct address exists but should not dominate.
9. **The NPC must have an agenda for speaking.** Every Dialogue blob exists because the NPC wants something, knows something, or needs to express something. Pure flavor with no point is not Dialogue.
10. **No meta-dialogue.** The NPC never comments on the conversation itself ("As I was saying," "Let me explain," "Listen carefully"). They just speak.

### Consecutive Dialogue Blobs
11. Dialogue has an adjacency limit of 1 in the breakdown — two Dialogue blobs should never appear back-to-back. If the breakdown violates this, flag it.

## What Dialogue Blobs Cover

Dialogue is the most character-driven blob. Use it for:

- **Quests & goals**: An NPC gives the main character a task, direction, or objective.
- **Information delivery**: Lore, warnings, directions, secrets — conveyed through personality rather than exposition.
- **Antagonism & motivation**: An NPC provokes, threatens, mocks, or challenges — creating emotional stakes.
- **Plot reveals**: Twists, betrayals, hidden connections surfaced through speech.
- **World reaction**: Showing how the main character's presence or actions affect the people around them. This is Dialogue's unique strength — it's the primary blob for making "you" feel consequential.

Dialogue is **not** for:
- The main character's own voice (they are "you," silent)
- Environmental description (Description)
- Guidebook instructions (Action)
- An omniscient narrator with meta-knowledge (Narrator)
- Structured lists or mechanics (Table)

## Tone

The NPC should sound like a *person* — with verbal habits, priorities, and a way of seeing the world. The four lines are a compressed window into someone's personality. They don't need to be eloquent; they need to be specific to that character.

Avoid:
- Generic NPC-speak ("Greetings, traveler. I have a task for you.")
- All four lines at the same emotional register — let the speech shift across the four beats
- Exposition dumps with no personality coloring the delivery
- Ending every line with a period — vary punctuation (questions, dashes, ellipses, fragments)

## Workflow

1. **Read the full breakdown** to understand the scene arc and where Dialogue blobs sit in the sequence.
2. **Identify the named NPC** for each Dialogue blob (from the breakdown header: `## N. DIALOGUE — [Character Name]`).
3. **Determine the NPC's agenda.** What do they want from this exchange? What are they trying to accomplish by speaking?
4. **For each Dialogue blob**, use the breakdown bullets as a content guide. The bullets say *what* the NPC conveys; you decide *how* they say it — vocabulary, cadence, attitude, sentence structure.
5. **Verify every hard rule**: exactly 4 lines, word counts per line and total, length variety, "you/your" limit, no stage directions, NPC has agenda, blockquote formatting.
6. **Output only the Dialogue blobs** under their original numbered headers.

## Output Format

```markdown
# [Scene Title] — Dialogue Blobs

## 5. DIALOGUE — [Character Name]

> "First line of speech."
> "Second line."
> "Third line — could be longer, with more detail or a different thought."
> "Fourth."
```

Name the output file `[Scene-Title]-Dialogue-Blobs.md`.

**CRITICAL:** Output ONLY Dialogue blobs. Do not write other blob types. Do not renumber.

## Examples

## 3. DIALOGUE — The Cunning Woman

> "In sooth, I came hither what time I marked thy tread upon the heather.
> "I trow not thy errand, yet ken that thou seekst rede or remedy.
> "Nettles and spit on the wights yclept 'Mancers'. Greater witching's in the wit.
> "Get thee to Yellowmoor, yon manor. The hypnotist shall hew whate'er works thee woe."

## 7. DIALOGUE — The Barber-Surgeon

> "Your body is a cracked teacup. Placing YOU back in yourself was- laborious.
> "Now the debt. Your Lady cannot pay for your life, so you must pay yourself.
> "The grave of Mool — a grot — is three days north along a parched riverbed. The grot were long ago slain and mummified.
> "Go there. The spit of Mool is the only currency I will take."

## 12. DIALOGUE — R the Killer

> "Escaping? Same. The name's R the Killer. I've just bust out of their gibbets.
> "I'm no sympathist, but two red hands are better than one.
> "They'll be locking the gate soon. What say you?
> "Team?"
