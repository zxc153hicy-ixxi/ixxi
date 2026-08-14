# Quotes Mode Reference

Abstract character-defining quotes into portable templates that preserve rhetorical shape and voice without locking into specific phrasing.


## Transformation Rules

**Capture:**

- Sentence count and relative lengths (e.g., "short punch, then long elaboration")
- Rhetorical structure (declaration, warning, paradox, rhetorical question, reframing)
- Emotional register (defiant, serene, sardonic, mournful, dignified)
- Relationship to addressee (peer, subordinate, enemy, self, no one)
- Core philosophical move (justifying, accepting, refusing, warning, revealing)

**Replace:**

- Proper nouns → role/relationship terms
- Setting-specific items → category (poetry → solitary art, courts → political arena)
- Cultural references → archetypal equivalents

**Preserve explicitly:**

- Rhythmic pattern and sentence architecture
- Key rhetorical devices (triadic contrast, paradox, rhetorical question)
- Tonal markers (formal, intimate, theatrical, aphoristic)
- The emotional truth that makes the quote character-defining

**Do not create:**

- Skeleton templates with bracketed placeholders (e.g., "I prefer [ART] to [POLITICS]")
- These over-constrain rewrites and flatten the quote's music

## Output Components

Each abstractd quote produces three elements:

**Structure** (1 sentence, 5-15 words)
The rhetorical skeleton: what move the quote makes, in what order.

**Rhetorical DNA** (3-5 bullets)
The specific devices, rhythms, and tonal qualities that give the quote its voice. This is what a rewrite must preserve to feel like the same kind of utterance.

**Respecification Seed** (1 sentence, 5-15 words)
The dramatic situation that calls for this quote—when and why a character would say something like this.

## Calibration Examples

| Original                                                                                                                                    | Structure                                                                | Rhetorical DNA                                                                                                                                                                                                   | Respecification Seed                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| "You forget, my friend. I have been a recluse, preferring poetry to courts and swords."                                                     | Gentle correction + self-declaration of withdrawal from X in favor of Y. | Two sentences, second longer. Direct address ("my friend") establishes warmth despite distance. Triadic contrast: solitary art vs political sphere + violence. Register: dignified, unhurried, no defensiveness. | A character who has chosen contemplative isolation explains this without apology when their past is assumed.         |
| "Manufacture dooms in your head and you will go mad. Reality is incontrovertible. Also, it will not be anticipated."                        | Warning against anxious speculation + terse philosophical anchor.        | Three short sentences, aphoristic. First: vivid consequence of mental habit. Second and third: clipped declarations. Register: hard-won wisdom, no softening.                                                    | A character counsels against catastrophizing, speaking from experience of having done exactly that.                  |
| "Who dares call me turncoat, who do but follow now as I have followed this rare wisdom all my days: to love the sunrise and the sundown..." | Defiant self-justification reframing apparent vice as aesthetic virtue.  | Rhetorical question structure. Reframes disloyalty as philosophical consistency. Elevated, theatrical register. Long flowing syntax mirrors the "following" being described.                                     | A character accused of betrayal refuses shame, instead claiming their inconstancy as a principle.                    |
| "I am supposed to talk to people!"                                                                                                          | Frustrated assertion of professional identity against circumstances.     | Single sentence, exclamatory. Emphasis on role/function ("supposed to"). Register: exasperated, almost comic indignation.                                                                                        | A character with a specific skill set finds themselves in a situation that renders that skill useless, and protests. |

## Workflow

1. User provides quote list (or references existing document)
2. For each quote, extract Structure, Rhetorical DNA, and Respecification Seed
3. Output in grouped format (all three elements per quote)

## Final Output

Create both output files:

1. **Markdown output**: Copy template from `assets/Quotes-Template.md`
2. **JSON output**: Copy template from `assets/quotes-template.json`

**Save as:**
- `[Character]-Quotes-Abstractd.md`
- `[character]-quotes-abstractd.json`