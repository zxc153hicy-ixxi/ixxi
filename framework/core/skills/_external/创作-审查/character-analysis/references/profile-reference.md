# Profile Mode Reference

Character profile analysis — structured breakdown using Purpose/Believe/Care/Invest framework.

## Character Type

Determine analysis depth based on character role:

**Main character**:
→ Fill ALL sections: Purpose, Believe, Care, Invest
→ DO NOT ADD SECTIONS/FIELDS TO THE TEMPLATE FILES

**Secondary character**:
→ Fill ONLY: Purpose
→ Remove other sections from the docs
→ DO NOT ADD SECTIONS/FIELDS TO THE TEMPLATE FILES

If unspecified, infer from character's narrative importance or ask user.

## Phase 1: Gather Sources

Use web_search to find substantive analysis:

1. Literary criticism and serious analysis of the character
2. Author/director/designer commentary on characterization techniques
3. Analysis of defining scenes

Example queries:
- `"[character] literary analysis"`
- `"[character] character study essay"`
- `"[author] characterization [character]"`
- `"[character] arc meaning symbolism"`

For secondary characters, 1-2 searches may suffice.

## Phase 2: Synthesize

Cross-reference findings. Note where common interpretations diverge from textual evidence. Identify symbolic patterns, recurring imagery, authorial intent.

## Phase 3: Generate Output

Copy templates from `assets/` to working directory, then fill:

1. **Markdown template** (`Character-Template.md`): Replace "Text" placeholders with concise answers (<8 words each)
2. **JSON template** (`character-template.json`): Fill values with single words where possible, short phrases only when necessary

Guidelines:
- Leave fields empty string if not applicable
- For arrays, use 4 items maximum
- Secondary characters: fill Purpose only, remove other sections
- **REMINDER**: DO NOT ADD SECTIONS/FIELDS TO THE TEMPLATE FILES (no "metadata", "Additional Analysis Notes", "Critical Reception", etc.)

Save as:
- `[Character]-Analysis.md`
- `[character]-analysis.json`
