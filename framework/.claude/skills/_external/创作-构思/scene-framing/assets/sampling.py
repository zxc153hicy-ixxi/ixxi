import argparse
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Usage:
# - 'python sampling.py archaisms 5'
# - 'python sampling.py archaisms' for the full array

VOCAB_PATH = Path(__file__).parent / "vocabulary.json"


def sample(array_name: str, n: int | None = None) -> list:
    with VOCAB_PATH.open(encoding="utf-8") as f:
        vocab = json.load(f)

    if array_name not in vocab:
        raise KeyError(f"'{array_name}' not found. Available: {', '.join(vocab.keys())}")

    arr = vocab[array_name]
    if n is None:
        return arr
    if n > len(arr):
        raise ValueError(f"Requested {n} elements but '{array_name}' has only {len(arr)}.")
    return random.sample(arr, n)


def main() -> int:
    parser = argparse.ArgumentParser(description="Randomly sample from vocabulary.json arrays.")
    parser.add_argument("array_name", help="Name of the array in vocabulary.json")
    parser.add_argument("n", nargs="?", type=int, default=None, help="Number of elements to sample (optional)")
    args = parser.parse_args()

    try:
        results = sample(args.array_name, args.n)
    except (KeyError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for item in results:
        print(item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
