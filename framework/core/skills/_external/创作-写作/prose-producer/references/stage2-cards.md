Read ONLY these two files plus files inside the `scene-framing` skill folder:
- Scene brief: `{SCENE_BRIEF_PATH}`
- Source passage: `{SOURCE_PATH}`

Use scene-tag `{SCENE_TAG}` for the output filename.

Invoke the `scene-framing` skill to produce all four card types in a single document:
- Scene parameters (uses the scene brief)
- Source imprint (uses the source passage)
- Speech rules — one card per speaking character mentioned in the scene brief's "Scene Outline"
- Forbidden patterns in PREDICTIVE mode (uses the scene brief)

Do not read any files outside the two listed inputs and the skill folder. Do not write anywhere except `output/`.

Report back the absolute path of the single scene-frame file written.
