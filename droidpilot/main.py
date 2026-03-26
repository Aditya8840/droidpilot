import argparse
import os
import sys

from dotenv import load_dotenv

from . import adb
from .agent import run


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="droidpilot",
        description="AI agent that operates your Android phone via ADB",
    )
    parser.add_argument("prompt")
    parser.add_argument(
        "--model",
        default=os.getenv("DROIDPILOT_MODEL", "gpt-4o"),
    )
    parser.add_argument("--max-steps", type=int, default=30)

    args = parser.parse_args()

    try:
        adb.check_adb_installed()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        run(args.prompt, model=args.model, max_steps=args.max_steps)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
