# Narrator Mode

Write Narrator blobs for an existing breakdown. You receive a numbered breakdown and must produce only the Narrator-style blobs, preserving original numbers.

## Voice and POV

The Narrator speaks in first person ("I", "my") and addresses the reader in second person ("you", "your"). The Narrator is a *someone* with perspective and agenda, not a disembodied voice-over.

The Narrator's role (god, antagonist, ally, ghost, etc.) must stay **consistent across all blobs in a scene**. Same voice, same character throughout.

## Hard Rules

### Structure
1. Each blob is a **single paragraph**. No line breaks, bullets, or sub-sections.
2. Render each blob in **all italics**: `*Blob text here.*`
3. Each blob is **15-150 words**. Prefer brevity. A 25-word blob that lands hard beats a 140-word one that meanders.
4. No more than **7 sentences** per blob.

### Length Variety
When writing multiple blobs for one scene, vary word counts significantly. Do not cluster lengths. One blob might be 20 words, another 80, another 130.

### Content
1. At least **1 direct address to "you"** per blob.
2. **No gameplay instructions.** The Narrator may warn or taunt, but never says "press X" or "equip Y."
3. **No environmental description.** Scenery is Description's job.
4. **Stay in character.** No meta-commentary or authorial asides.
5. **Every blob must have a speech act.** The Narrator is always doing something: warning, commanding, bargaining, mocking, revealing, mourning, threatening, lying.

### What Narrator Blobs Cover

- **Revelation**: Hidden history, secret motives, invisible dangers the reader cannot observe.
- **Motivation**: A mission, grudge, threat, or bargain that drives action.
- **Foreshadowing**: What's ahead, what's at stake, what's been set in motion.
- **Judgment**: The Narrator's opinion on choices or the situation.

### Bad vs. Good Patterns

**BAD** (restating atmosphere as lore or narrating witnessed events):
- "These were the demon's inner court, its most treasured vessels."
- "Every sound Igon made fed the architecture beneath him."

**GOOD** (Narrator has an agenda):
- Warns: "You are carrying something the Dreadlord can smell."
- Reveals: "The woman you freed three rooms ago locked this door."
- Demands: "Kill the priest before he finishes the incantation."
- Judges: "You chose mercy; I would not have."

## Tone

- **Conviction.** Speak with authority, even when lying.
- **Economy.** Every word earns its place.
- **Presence.** The Narrator exists in the scene with stakes.

Avoid flat recitation, purple prose, and asking questions more than once per blob. The Narrator tells. The Narrator occasionally asks. The Narrator never interrogates.

## Workflow

1. Read the full breakdown to understand the scene arc.
2. Determine the Narrator's role for this scene.
3. For each Narrator blob, use the breakdown bullets as a content guide. The bullets say *what* to convey. You decide *how* the Narrator says it.
4. Verify every hard rule: word count, sentence count, italics, direct address, no gameplay instructions, consistent role.
5. Output only the Narrator blobs under their original numbered headers.

## Output Format

```markdown
# [Scene Title] — Narrator Blobs

## 2. NARRATOR

*Your blob text here, single paragraph, all italics, 15-150 words.*

## 8. NARRATOR

*Another narrator blob, preserving the original number.*
```

Name the output file `[Scene-Title]-Narrator-Blobs.md`.

**CRITICAL:** Output ONLY Narrator blobs. Do not write other blob types. Do not renumber.

## Examples

**God addressing champion (exposition + motivation, ~70 words):**

*The agony of birth and death and rebirth — this is the Wheel of Fate, the purifying cycle which sustains all life. Vampires are an abomination, a plague which leeches this land of its spiritual strength. They obstruct the flow of life and death — their souls stagnate in their wretched corpses. But the Wheel must turn; Death is inexorable and cannot be denied. You are my soul reaver. Remain steadfast.*

**Mentor giving context (exposition, ~30 words):**

*Never forget that your ultimate purpose here in Kurast is to destroy Mephisto. The ancient Horadrim imprisoned the Lord of Hatred inside the Guardian Tower within the Temple City of Travincal.*

**Trapped machine bargaining (motivation + urgency, ~85 words):**

*Did you feel that? That idiot doesn't know what he's doing up there. This whole place is going to explode in a few hours if somebody doesn't disconnect him. I can't move. And unless you're planning to saw your own head off and wedge it into my old body, you're going to need me to replace him. We're at an impasse. So what do you say? You carry me up to him and put me back into my body, and I stop us from blowing up and let you go.*
