# Actions Mode Reference

Generate chronological list of significant actions a character takes.

## Phase 1: Gather Sources

Search for comprehensive plot coverage:

1. Detailed plot summaries and synopses
2. Chapter/episode/book breakdowns
3. Wiki pages with chronological coverage
4. Timeline resources

Example queries:
- `"[character] [work title] plot summary"`
- `"[work title] chapter summary"` or `"[work title] book by book summary"`
- `"[character] wiki"` (then web_fetch the result)
- `"[work title] timeline events"`

For long works (epics, series), search by arc/section:
- `"[work title] book 1 summary"`, `"[work title] book 2 summary"`, etc.
- `"[character] [arc name] actions"`

Use `web_fetch` on detailed wiki pages or plot breakdowns to get comprehensive coverage.

## Phase 2: Synthesize

Build chronological list of significant actions. Distinguish what character *does* from what *happens to* them.

## Phase 3: Generate Output

**Action criteria:**
- 5-15 words each, single sentence
- Active verb phrase (character as subject doing the action)
- Significant: plot-moving, character-defining, or pivotal choices
- Concrete and specific (not vague summaries)

**Include:**
- Major plot actions and decisions
- Defining moral choices
- Key interactions with other characters
- Turning points and pivotal moments

**Exclude:**
- Passive events (things done TO the character)
- Internal states without external action ("feels sad", "realizes truth")
- Trivial actions unless character-defining

**Format:**
Copy template from `assets/Actions-Template.md` to working directory, then fill in list items as: 
1. [Action in active voice, 5-15 words]
2. [Action in active voice, 5-15 words]
...

**Order:** Chronological within the narrative.

**DO NOT ADD SECTIONS/FIELDS TO THE TEMPLATE FILES** (no "metadata", "Additional Analysis Notes", "Critical Reception", etc.)

Save as: `[Character]-Actions.md`
