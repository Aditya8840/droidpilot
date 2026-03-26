import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from . import adb
from .agent import run

logger = logging.getLogger("droidpilot")


def _setup_logging(*, verbose: bool = False, quiet: bool = False) -> None:
    """Configure the ``droidpilot`` logger.

    * Default level is INFO.
    * ``--verbose`` lowers it to DEBUG and adds timestamps.
    * ``--quiet`` raises it to WARNING.
    * When stderr is not a TTY (e.g. piped to a file), timestamps are always
      included so log lines can be correlated after the fact.
    """
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    is_tty = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

    if verbose or not is_tty:
        fmt = "%(asctime)s %(levelname)s %(message)s"
    else:
        fmt = "%(message)s"

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger("droidpilot")
    root.setLevel(level)
    root.addHandler(handler)


def main() -> None:
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

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show debug output with timestamps",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="only show warnings and errors",
    )

    args = parser.parse_args()

    _setup_logging(verbose=args.verbose, quiet=args.quiet)

    try:
        adb.check_adb_installed()
    except RuntimeError as e:
        logger.error("Error: %s", e)
        sys.exit(1)

    try:
        run(args.prompt, model=args.model, max_steps=args.max_steps)
    except RuntimeError as e:
        logger.error("Error: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Aborted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
