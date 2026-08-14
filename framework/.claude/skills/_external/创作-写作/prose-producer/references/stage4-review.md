Read ONLY these files plus files inside the scene-review skill folder:
- Scene draft: `{SCENE_DRAFT_PATH}`
- Scene brief: `{SCENE_BRIEF_PATH}`
- Scene frame from Stage 2: `{SCENE_FRAME_PATH}`

Do NOT read the source style passage, the full story outline, the prior scene file, or any other file.

Invoke the `scene-review` skill, following its workflow exactly. Use the scene brief as the source for story background, scene outline, wordcount, and scene type (infer establishing vs continuation from the outline if not stated). Treat every section of the scene frame as binding constraints during the revision pass; the revised prose must continue to honor them.

The scene file is revised in place at `{SCENE_DRAFT_PATH}`. Write the post-scene summary file under `output/`, named to match the scene file (e.g., if the scene is `Storyname-Scene-X.md`, write `Storyname-Scene-X-Summary.md`).

Report back the absolute paths of the revised scene file and the post-scene summary file.
