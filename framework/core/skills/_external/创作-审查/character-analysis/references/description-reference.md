# Description Mode Reference

Generate physical description of a character based on source material. Focus exclusively on sensory details — what can be seen, heard, smelled, touched. Do NOT include personality, tone, or internal states.

## Phase 1: Search Strategy

**Goal:** Find verbatim source text first. Synthesis is fallback.

### Search Query Progression

Start specific, broaden if needed:

```
Round 1 - Direct quotes:
"[character]" "[work title]" "appeared" OR "looked" OR "described"
"[character]" "[work title]" physical description
"[character]" "[work title]" appearance quote

Round 2 - Wiki/reference:
[character] [work title] wiki appearance
[character] [work title] fandom appearance section
[character] site:tvtropes.org (check Character page for description)

Round 3 - Visual media (games/film/animation):
[character] [work title] character design
[character] [work title] concept art description
[character] [work title] model viewer
```

### Evaluate Search Snippets First

Before any fetch, check if snippets contain:
- Direct quoted passages
- Specific physical details (hair, eyes, build, distinguishing marks)
- Enough detail to fill core template fields

**If snippets contain quoted source text, attempt fetch for fuller context**

## Phase 2: Fetch Strategy

### Fetch Rules

1. **Attempt max 2 fetches total** — not 2 per source type
2. **Prioritize in order:**
   - `.txt`, `.htm`, or `.html` pages containing source text
   - Wiki page with confirmed "Appearance" section (check URL or snippet for indicator)
   - TVTropes character page
   - Fan sites with quoted passages
3. **On fetch failure:** Do NOT retry same domain. Move to next source or fall back to snippet synthesis.

## Phase 3: Synthesize

Compile findings into the description template fields.

**Strict rules:**
- Only fill fields with directly stated or clearly visible information
- Do NOT infer unstated details (e.g., don't guess smell if not mentioned)
- Exception: `symbolic_animal` should always be filled — infer a best-guess if not explicit
- **DO NOT LIST NON-PHYSICAL DETAILS** such as mood, personality, occupation, etc

**For the Full Description:**
- If source text is 250-500 words: use verbatim (mark with quotes)
- If source text is shorter: **include quoted source text**, then augment with other research
- If source text is longer: **include most relevant quoted passages**
- `Reminder`: description must be 1-2 paragraphs long, 250-500 words

## Phase 4: Generate Output

Create both output files:

1. **Markdown output**: Copy template from `assets/Description-Template.md`, fill in ONLY applicable fields
2. **JSON output**: Copy template from `assets/description-template.json`, fill in ONLY applicable fields

**Save as:**
- `[Character]-Description.md`
- `[character]-description.json`
