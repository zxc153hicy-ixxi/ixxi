---
name: scene-audit
description: Audit a finished scene draft against the larger story outline. Produces two terse lists of suggested edits — one for story-context fit, one for internal quality (awkward, confusing, or contradictory passages). Triggers include "scene audit", "audit scene", "review scene against outline".
---

# Scene Audit

Read ONLY these inputs:
- The scene draft
- The full story outline
- The prior scene's prose (if provided — may be omitted for scene 1)

Analyze on two fronts:

1. **Story fit** — Does the scene serve the larger story? Flag any line, paragraph, or moment that breaks the original intention, contradicts established facts, or pulls focus from the scene's purpose in the arc. Pay close attention to the original scene's role in the larger context.
2. **Internal quality** — Flag awkward phrasing, confusing passages, internal contradictions, or muddled cause-and-effect within the scene itself. If a prior scene was provided, also flag any sentence or paragraph that re-describes character appearances, setting features, or sensory details already rendered in that prior scene's prose.

## Output

A markdown card with two top-level lists, in this order:

```
# Scene Audit — [scene-tag]

## Story Fit
- **[recommendation]** — [one-line justification]
  > "[exact line or passage]"

## Internal Quality
- **[recommendation]** — [one-line justification]
  > "[exact line or passage]"
```

Each item must be brief: a sharp recommendation, one short justification, and the exact line/passage being flagged.

If a list has no findings, say "None." under that heading.

Do not add extra categories to your card.

 Keep your card under 300 words.

Save to `output/scene-audit-[scene-tag].md`.
