import argparse
import json
import random
from pathlib import Path

# Usage:
# - 'python build_voice.py' writes to Voice.md
# - 'python build_voice.py Voice-2.md' writes to the given filename (in this folder)

HERE = Path(__file__).parent
VOCAB_PATH = HERE / "vocabulary.json"
TEMPLATE_PATH = HERE / "voice_template.json"
DEFAULT_OUTPUT = "Voice.md"


def format_sample(items: list[str], fmt: str) -> str:
    if fmt == "lines":
        return "\n\n".join(items)
    if fmt == "blockquote_lines":
        return "\n".join(f"> {x}" for x in items)
    if fmt == "blockquote_comma":
        return "> " + ", ".join(items)
    if fmt == "inline_comma":
        return ", ".join(items)
    raise ValueError(f"Unknown format: {fmt}")


def build(output_path: Path) -> None:
    with VOCAB_PATH.open(encoding="utf-8") as f:
        vocab = json.load(f)
    with TEMPLATE_PATH.open(encoding="utf-8") as f:
        template = json.load(f)

    parts: list[str] = []
    for block in template:
        kind = block["type"]
        if kind == "static":
            parts.append(block["text"])
        elif kind == "sample":
            source = block["source"]
            n = block["n"]
            arr = vocab[source]
            if n > len(arr):
                raise ValueError(f"Requested {n} from '{source}' but only {len(arr)} available.")
            items = random.sample(arr, n)
            parts.append(format_sample(items, block["format"]))
        else:
            raise ValueError(f"Unknown block type: {kind}")

    output_path.write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Voice.md from voice_template.json and vocabulary.json.")
    parser.add_argument("filename", nargs="?", default=DEFAULT_OUTPUT, help="Output filename (written to this folder).")
    args = parser.parse_args()
    build(HERE / args.filename)
