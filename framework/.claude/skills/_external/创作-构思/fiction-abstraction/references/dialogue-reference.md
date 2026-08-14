# Dialogue Mode Reference

Abstract fiction dialogue exchanges into portable templates that preserve conversational shape and dynamics without locking into specific content.

## Transformation Rules

**Capture:**

- Beat count and rhythm (e.g., "four beats: query, deflection, pressed query, cryptic yield")
- Power dynamic between speakers (who pursues, who withholds)
- Line length contrast (terse vs. weighted, clipped vs. ornate)
- Interstitial action style (minimal gesture, loaded silence, environmental reaction)

**Replace:**

- Proper nouns → role/relationship terms
- Setting-specific items → category (throne room → seat of power, prophecy → revelation)
- Cultural references → archetypal equivalents

**Preserve explicitly:**

- Exchange shape (the choreography)
- Speech rhythm contrast between speakers
- Interstitial placement and function (where action beats punctuate)
- Tonal register (formal, intimate, threatening, cryptic)

**Do not create:**

- Line-by-line templates with bracketed placeholders
- These fragment the exchange and flatten conversational music

## Output Components

Each abstracted exchange produces these elements:


**Word Count** (bucket)
Total for full exchange. Must be one of:
0-50, 50-100, 100-150, 150-200, 200-250, 250+

**Exchange Type**
Must be one of:
- Interrogation: One speaker extracts, one resists
- Negotiation: Both speakers want something
- Revelation: One delivers information, one reacts
- Confrontation: Mutual challenge
- Counsel: One advises or warns, one weighs the words
- Ritual: Formal exchange (oaths, greetings, ceremonies)

**Tension Arc**
Must be one of:
- Escalate: builds pressure
- Release: dissipates pressure
- Maintain: holds steady state

**Beat Count** (bucket)
Number of back-and-forth volleys. Must be one of:
2-3, 3-4, 4-6, 6+

**Exchange Shape** (1 sentence, 5-15 words)
The thrust-parry pattern in shorthand (e.g., "query → deflection → pressed query → cryptic yield")

**Structure** (1-3 sentences, 5-30 words)
Beat progression and interstitial guidance: where action beats fall, how the exchange opens and closes.

**Rhetorical DNA** (3-5 bullets)
The specific dynamics that give the exchange its character

**Respecification Seed** (1 sentence, 5-15 words)
The dramatic situation that calls for this exchange. See calibration examples for proper generality.

## Calibration Examples

These examples show proper abstraction level vs. over-specific output that limits reuse.

| Component  | Too Specific                                                                                           | Properly Abstracted                                                                                |
| ---------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Structure  | "Opens with authority's sour dismissal demanding explanation"                                          | "Opens with antagonist demanding explanation"                                                      |
| Structure  | "Advisor delivers elaborate prophetic vision"                                                          | "Actor delivers elaborate prophetic vision"                                                        |
| Structure  | "Authority explodes into multi-part accusation spanning jealousy, disloyalty, and conspiracy"          | "Antagonist explodes into multi-part accusation of motives (examples: jealousy, disloyalty, fear)" |
| Structure  | "Captive answers obliquely with partial information"                                                   | "Antagonist answers obliquely with partial information"                                            |
| DNA bullet | "Power asymmetry: absolute authority vs. vulnerable counselor; one speaks volumes, one barely defends" | "Power asymmetry: absolute antagonist vs. vulnerable actor; one speaks volumes, one defends"       |
| DNA bullet | "Captors hold all leverage but use soft extraction; captive is wary, broken, speaks from trauma"       | "Interrogator holds leverage but uses soft extraction; antagonist is wary"                         |
| DNA bullet | "Subtext: advisor genuinely fears for king; king suspects political maneuvering behind every word"     | (Omit - too specific to single scenario)                                                           |
| Seed       | "A counselor's sincere warning interpreted as scheming by a paranoid ruler"                            | "An actor's sincere warning interpreted as scheming by a paranoid antagonist"                      |
| Seed       | "Interrogators coax information from a traumatized, suspicious captive using kindness"                 | "Interrogator coaxes information from a suspicious antagonist using kindness"                      |

## Workflow

1. User provides dialogue exchange(s) (or references existing document)
2. For each exchange, extract all components
3. Output in grouped format

## Final Output

Create both output files:

1. **Markdown output**: Copy template from `assets/Dialogue-Template.md`
2. **JSON output**: Copy template from `assets/dialogue-template.json`

**Save as:**
- `[Work]-Dialogue-Abstracted.md`
- `[Work]-dialogue-abstracted.json`
