# Quotes Mode Reference

Generate a list of significant quotes or statements made by a character. Focus exclusively on **character-defining quotes**, words representing core beliefs. Do NOT include quotes just because they are memorable.

## Phase 1: Gather Sources

**ALL QUOTES MUST BE VERBATIM FROM THE SOURCE**.

**Search queries:**
- `"[character]" "[work title]" quotes`
- `"[character]" said site:fandom.com`
- `"[character]" [work] dialogue transcript`
- `"[character]" [work] filetype:txt` (for plain text sources)

**For books specifically:**
- `[character] [work] "he said" OR "she said"`

**Fetching (optional, expect failures):**
- Try Fandom wikis first (most permissive)
- Archive.org cached versions as backup
- Skip wikiquote, IMDB, quotes.net — these block bot access

**Fallback:** If fetches fail or return errors, rely on search snippets and training knowledge of the work.

## Phase 2: Synthesize

Build chronological list of *significant* quotes spoken by the character. Distinguish phrases that define the character's *core*, not just *most memorable* sayings.

## Phase 3: Generate Output

**Quote criteria:**
- `30 words maximum` each
- `10 total quotes maximum`
- `Significant`: character-defining or pivotal-decisions

**Include:**
- Quotes expressing core beliefs
- Quotes involving key story decisions
- Key statements made to other people
- Turning point or moral decision quotes

**Exclude:**
- Quotes by other characters *about* the character
- Internal thoughts without spoken words
- Popular quotes that do not define the character

**Format:**
Copy template from `assets/Quotes-Template.md` to working directory, fill in:
1. [Quote, 1-30 words]
2. [Quote, 1-30 words]
...

**DO NOT ADD SECTIONS/FIELDS TO THE TEMPLATE FILES** (no "metadata", "Additional Analysis Notes", "Critical Reception", etc.)

Save as: `[Character]-Quotes.md`