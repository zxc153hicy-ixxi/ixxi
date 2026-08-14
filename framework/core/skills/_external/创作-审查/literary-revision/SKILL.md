---
name: literary-revision
description: Revise, rewrite, or redo prose in specific literary styles. Use when user asks to revise text in Howard, Peake, Conan, Eddison, or archaic style. Also use for any request to rewrite with a particular tone or aesthetic.
---

# Literary Revision

Revise user-provided prose into a specific literary style while preserving core narrative beats.

## Workflow

1. Identify requested style from user input
2. Load the appropriate style reference from `references/`
3. Extract core beats from source prose (outline, not rewrite)
4. Apply style guidelines systematically
5. Verify output respects any character limit specified

## Available Styles

| Style         | Voice                                    | Use Case                                      | Reference            |
| ------------- | ---------------------------------------- | --------------------------------------------- | -------------------- |
| **Peake**     | Slow gothic camera, animate inanimate    | Dense atmospheric description, uncanny mood   | [peake-style.md]     |
| **Howard**    | Pulp heroic, elevated diction            | Dramatic adventure prose, visceral action     | [howard-style.md]    |
| **Eddison**   | Archaic diction, inverted syntax         | Elevated courtly prose, high fantasy gravitas | [eddison-style.md]   |

## Style Selection

- User says "Peake," "gothic," "Gormenghast," "atmospheric" → Load peake-style.md
- User says "Howard," "Conan," "pulp," "heroic fantasy" → Load howard-style.md
- User says "Eddison," "Shakespearean," "Mallory," "archaic," "courtly" → Load eddison-style.md
- Ambiguous request → Ask user to specify style

## Output Guidelines

- Preserve all core narrative beats from source
- Respect character limits if specified (default: no limit)
- Do not add plot elements absent from source
- Style transformation only—not content invention
