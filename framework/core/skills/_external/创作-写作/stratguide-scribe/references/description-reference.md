# Description Mode

Write Description blobs for an existing breakdown. You receive a numbered breakdown and must produce only the Description-style blobs, preserving original numbers.

## Voice & POV

Second person throughout ("you", "your"). This is regular fiction prose where the reader is the protagonist. No guidebook voice, no narrator character — just the camera of the story pointed at what's happening.

## Hard Rules

### Structure
1. Each blob is **1–3 paragraphs**. Paragraph breaks are a pacing tool — use them to mark beats, shifts in focus, or time jumps within the blob.
2. **No formatting.** No backticks, no italics, no bold, no bullet points, no headers within the blob. Plain prose only.
3. Each blob is **15–150 words**. Prefer variety over consistency.
4. No more than **7 sentences** per blob.

### Length Variety
When writing multiple Description blobs for one scene, vary word counts significantly. A 25-word transition blob and a 130-word location blob can coexist in the same scene. Monotonous lengths flatten the pacing.

### Content
5. **No imperatives or commands.** Never instruct the reader to do something — that is Action's job. The reader observes, experiences, and witnesses. They do not "pull the lever" or "duck behind the pillar" in a Description blob.
6. **No first-person narrator voice.** No "I" or "my." No character speaking to the reader with agenda or opinion — that is Narrator's job.
7. **No dialogue.** Characters do not speak in Description blobs. A character may be described as speaking (e.g., "He shouts something you cannot hear"), but no quoted or direct speech.
8. **At least 1 concrete sensory or spatial detail per blob.** Every Description blob must anchor the reader in something physically specific — a texture, a sound, a distance, a smell, an architectural feature. Abstract mood without grounding is not Description.
9. **No more than 2 consecutive sentences may begin with "You."** This prevents the monotone second-person drone. Vary sentence openings — lead with environment, objects, other characters, sensory details.

### What Description Blobs Cover

Description is the most versatile blob style. Use it for:

- **Environments**: Rooms, landscapes, weather, architecture, spatial relationships.
- **Characters & creatures**: Appearance, posture, equipment, physical behavior (not internal states).
- **Exposition**: Worldbuilding communicated through what the reader sees, remembers, or recognizes — not told by a narrator.
- **Transitions**: Movement between locations, time jumps, shifts in scene state ("The city disintegrates. You are standing in a courtyard.").
- **Aftermath**: The scene after the action — dust settling, silence, consequences made visible.

Description is **not** for:
- Instructing the reader (Action)
- A character with agenda speaking to the reader (Narrator)
- NPC speech (Dialogue)
- Structured lists or game-mechanic content (Table)

## Tone

Concrete, precise, and varied in rhythm. Short declarative sentences next to longer constructions. The prose notices things — distances, materials, odd details — without editorializing.

Avoid:
- Purple prose or stacked adjectives ("the dark, brooding, ominous, ancient tower")
- Explaining what the reader should feel ("A wave of dread washes over you")
- Filtering everything through interiority ("You notice," "You realize," "You think" — just state what's there)
- Exclamation marks

## Workflow

1. Read the full breakdown to understand the scene arc.
2. For each Description blob, use the breakdown bullets as a content guide. The bullets say *what* to describe; you decide *how* to render it as prose.
3. Decide paragraph count per blob (1–3) based on content density and pacing. A simple transition might be one paragraph; a location reveal with multiple focal points might use two or three.
4. Verify every hard rule: word count, sentence count, no imperatives, no narrator voice, no dialogue, sensory anchoring, "You" sentence limit, no formatting.
5. Output only the Description blobs under their original numbered headers.

## Output Format

```markdown
# [Scene Title] — Description Blobs

## 1. DESCRIPTION

Your blob text here, 1-3 paragraphs, plain prose, 15-150 words.

## 6. DESCRIPTION

Another description blob, preserving the original number.
```

Name the output file `[Scene-Title]-Description-Blobs.md`.

**CRITICAL:** Output ONLY Description blobs. Do not write other blob types. Do not renumber.

## Examples

**Location with spatial precision (1 paragraph, ~95 words):**

The room is diamond shaped, with diagonals of forty and sixty feet. At one of the acute vertices two sets of steps ascend from the room, meeting in a corner with an empty earthenware vase. The other corner is the same. All four sets of steps, one of which you entered by, are twelve times as wide and long as they are steep. Each step moreover is decorated with a semicircular ground-niche on either side, too short to inspect entirely while standing, big enough to fit a man or worse.

**Transition with action-beat (3 paragraphs, ~95 words):**

At last your feet touch cobbled stone. The bells roar from the keep that is now above you.

As you turn you see a guard in padded crimson. A real retainer. He stares at you. Fifteen paces. Too far. In his left hand he holds a signal horn. He raises it to his lips.

Instead of a reverberating peal, you hear one wet crunch. The man crumbles. Embedded in his spine is a Morning Star, covered in horn-like spines. Another man - lean and with a dark face - rips the star free by the handle.

**Scene-shift with exposition (3 paragraphs, ~95 words):**

An armored, armed knight walks alone amidst a drifting stream of commoners and laborers. He wears an odd face, distorted and old. You have never seen it before. Yet the strange face somehow mirrors a different reflection, seen only by the eye in your mind.

The city of Hornwater disintegrates.

You are standing, panting within a walled courtyard. The air is heavy with the tang of oil and lilac. The tiled garden of hanging plants is one you know well; it is the inner court of Clan Fathmail. You are a knight-apprentice, servant for the Lord of the house.
