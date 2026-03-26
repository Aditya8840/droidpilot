import argparse
import os
import sys

from dotenv import load_dotenv

from . import adb
from .agent import run
from .providers import DEFAULT_MODELS, PROVIDERS


def main() -> None:
    load_dotenv()

    provider_names = sorted(PROVIDERS.keys())
    default_provider = os.getenv("DROIDPILOT_PROVIDER", "openai")
    default_model = os.getenv("DROIDPILOT_MODEL")

    parser = argparse.ArgumentParser(
        prog="droidpilot",
        description="AI agent that operates your Android phone via ADB",
    )
    parser.add_argument("prompt")
    parser.add_argument(
        "--provider",
        choices=provider_names,
        default=default_provider,
        help=f"LLM provider (default: {default_provider})",
    )
    parser.add_argument(
        "--model",
        default=default_model,
        help="Model name (defaults per provider: "
        + ", ".join(f"{k}={v}" for k, v in sorted(DEFAULT_MODELS.items()))
        + ")",
    )
    parser.add_argument("--max-steps", type=int, default=30)

    args = parser.parse_args()

    try:
        adb.check_adb_installed()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        run(
            args.prompt,
            provider=args.provider,
            model=args.model,
            max_steps=args.max_steps,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
