# Lemma Mode

Write the Lemma blobs for an existing breakdown. You are given a numbered breakdown file and must produce only the Lemma-style blobs, preserving their original numbers.

## Voice & POV

Lemmas are reference entries, not narrative. No POV, no "I," no "you," no emotional coloring. The writer is an invisible cataloger who simply knows. Register is scholarly and authoritative, like a page lifted from a worldly encyclopedia.

Tense is mixed, governed by time-relation to the entity:
- **Present** for enduring description and ongoing existence ("hilt is the shape of a serpent," "typical weight exceeds two tons").
- **Past** for origin, history, and completed events ("was made by a nameless mancer," "drove the Road through her land").

Hedging is required when reporting legend or unverified attribution: "is said to have," "reputed to," "according to...". Hedges separate fact from folklore inside the same entry.

## Hard Rules

These are non-negotiable. Violate none of them.

### Structure
1. **One entity per blob.** The entity name matches the breakdown header exactly (`## N. LEMMA — [Entity Name]`).
2. **Two allowed formats**: paragraph (a single prose block, no labels) or structured fields (a short list of labeled keys).
3. **Structured-field labels must vary per entity.** There is NO fixed menu. Do NOT reuse the same field set across entities in the same scene.
4. Choice between paragraph and structured format is a judgment call.

### Word Limits
5. **Per lemma**: 40-120 words total. This is a ceiling, not a target. Let the content dictate length. Terse is good.
6. **Vary lengths across lemmas in a scene.** If multiple lemmas appear, do not cluster them at the same word count. Mix a lean 45-word entry with a fuller 110-word entry.

### Tense
7. Apply the present/past rule above. Origin sentences are past; description sentences are present. Do use future tense.

### Image
8. **Every lemma carries an image placeholder** immediately below the header, in this format:

   `![IMAGE: short prompt describing desired image](images/entity-name.png)`

   The alt text is the image-generation prompt suggestion. The path slugs the entity name (lowercase, hyphenated) into the `images/` subfolder alongside the output file.

### Content
9. **No first or second person.** No "I," no "you," no "we," no "our."
10. **No narrator presence, no emotional coloring.** Clinical awe is fine; personal reaction is not.
11. **No questions.** No rhetorical devices addressed to the reader.
12. **Hedge legend from fact.** Use "is said to," "reputed," "according to..." when attesting to mythic or uncertain information.

## What Lemma Blobs Cover

Lemmas catalog a single canonical entity: creatures, items, locations, phenomena, materials, etc, etc. Use them as punctuation, anchoring information about something the reader has just encountered.

If the entity is generic or has no name, it probably belongs in an Essay, not a Lemma.

## Tone

Terse, omniscient, evocative. Each lemma should read as if lifted from a reference volume that took the entity for granted centuries ago. Let specific details carry the weight: names, measurements, attributions, side effects.

Avoid:
- Narrative framing ("The hero found...", "One will encounter...")
- Vague filler ("a powerful weapon," "a dangerous creature")
- Sentences beginning with "This is" or "There is"
- Questions or rhetorical address
- Repeating the same field labels across unrelated lemmas

## Workflow

1. **Read the full breakdown** to understand the scene arc and where Lemma blobs sit.
2. **Identify each Lemma blob** — note the entity name in the header and the bullets describing its essence.
3. **Choose format.** Paragraph for mythic or singular entities; structured fields for taxonomic or categorical entities. Either is valid.
4. **Pick structured-field labels fresh** for this specific entity if going structured. Do NOT reuse a default set.
5. **Draft prose.** Apply tense rule: past for origin, present for ongoing description. Hedge where attribution is legendary.
6. **Insert image placeholder** below the header with a short, specific generation prompt as alt text.
7. **Validate.** Word count 40-120. No first/second person. No questions. Fields varied (if structured). Image present.

## Output Format

```markdown
# [Scene Title] — Lemma Blobs

## 3. LEMMA — [Entity Name]

![IMAGE: short generation prompt](images/entity-name.png)

Paragraph lemma text, 40-120 words.

## 7. LEMMA — [Other Entity]

![IMAGE: different prompt](images/other-entity.png)

**Field A:** Value.
**Field B:** Value.
**Field C:** Value.
```

The output file should be named `[Scene-Title]-Lemma-Blobs.md`.

**CRITICAL:** Output ONLY Lemma blobs. Do not write blobs for any other style. Do not renumber — preserve the exact numbers from the input breakdown.