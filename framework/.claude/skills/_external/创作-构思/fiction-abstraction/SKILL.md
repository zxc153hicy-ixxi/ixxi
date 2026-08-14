---
name: fiction-abstraction
description: Abstract elements (paragraphs, dialogue, plots, scenes) from specific fictional sources. Use when asked to "abstract [elements]", make elements "more general", or create "reusable" or "generic" templates. Triggers include "abstract [elements] in [filename]", "make [element] generic", "strip [element] details".
---

# Fiction Abstraction

Transform fictional-work-specific elements into portable, reusable templates for writing.

## Mode Detection

Determine mode from user request:

**Paragraphs mode**:
- Triggers: "generic paragraphs", "abstract paragraphs", "list of generic paragraphs"
- **Read**: `references/paragraphs-reference.md`

**Dialogue mode**:
- Triggers: "generic dialogue", "abstract dialogue", "dialogue templates", "abstract exchanges"
- **Read**: `references/dialogue-reference.md`

If ambiguous, ask user which mode.

## Workflow

1. Detect mode from triggers above
2. Read the appropriate reference doc for that mode
3. Follow the workflow in that reference doc
4. Present completed file(s) to user
