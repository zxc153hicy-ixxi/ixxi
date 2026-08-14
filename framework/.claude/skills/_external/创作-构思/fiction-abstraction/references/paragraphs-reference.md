# Paragraphs Mode Reference

Abstract fition paragraphs into portable templates that preserve structural shape and voice without locking into specific content.

## Transformation Rules

**Capture:**

- Sentence count and length variation (e.g., "three short bursts, then one long unwinding")
- Rhetorical structure (build-up, reveal, contrast, accumulation)
- Emotional register (defiant, serene, sardonic, mournful, dignified)
- Core dramatic function (establishing, escalating, releasing, transitioning)

**Replace:**

- Proper nouns → role/relationship terms
- Setting-specific items → category (castle → stronghold, katana → blade)
- Cultural references → archetypal equivalents

**Preserve explicitly:**

- Rhythmic pattern and sentence architecture
- Key rhetorical devices (triadic structure, parallel construction, sentence fragment punch)
- Tonal markers (formal, intimate, theatrical, sparse)

**Do not create:**

- Skeleton templates with bracketed placeholders
- These over-constrain rewrites and flatten the paragraph's music

## Output Components

Each abstractd paragraph produces these elements:

**Word Count** (bucket)
Must be one of:
0-50, 50-100, 100-150, 150-200, 200-250, 250+

**Paragraph Type**
Must be one of:
- Action: movement, conflict
- Description: scene, character, sensory detail
- Exposition: backstory, context, transitions
- Reflection: what's felt/thought
- Dialogue: what's said

**Tension Arc**
Must be one of:
- Escalate: builds pressure
- Release: dissipates pressure
- Maintain: holds steady state

**Structure** (1-3 sentences, 5-30 words)
The rhetorical skeleton: sentence count, length variation, what move the paragraph makes.
- ALWAYS INCLUDE THE SENTENCE COUNT

**Rhetorical DNA** (3-5 bullets)
The specific devices, rhythms, and tonal qualities that give the paragraph its voice.

**Respecification Seed** (1 sentence, 5-15 words)
The dramatic situation that calls for this paragraph. See calibration examples for proper generality.

## Calibration Examples

These examples show proper abstraction level vs. over-specific output that limits reuse.

| Component  | Too Specific                                             | Properly Abstracted                                                                   |
| ---------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Structure  | "...climaxes with athletic boarding of a ship"           | "...climaxes with athletic feat"                                                      |
| DNA bullet | "Ship personified—loses headway, rolls helplessly"       | "Location personified—darkens or shifts soundscapes"                                  |
| DNA bullet | "Sword sings its death-song"                             | "Equipment given agency and sound (Example: sword sings its death-song)"              |
| Seed       | "A pursued figure escapes onto a departing vessel."      | "A moving figure makes a desperate maneuver onto a transport or through an obstacle." |
| Seed       | "A vessel's crew falls until a newcomer seizes command." | "A group falls one by one until a singular figure must act."                          |

## Workflow

1. User provides paragraph list (or references existing document)
2. For each paragraph, extract all components
3. Output in grouped format

## Final Output

Create both output files:

1. **Markdown output**: Copy template from `assets/Paragraphs-Template.md`
2. **JSON output**: Copy template from `assets/paragraphs-template.json`

**Save as:**
- `[Work]-Paragraphs-Abstracted.md`
- `[Work]-paragraphs-abstracted.json`
