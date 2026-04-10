"""Tests for droidpilot logging configuration."""

import logging

from droidpilot.main import _setup_logging


def _reset_logger() -> None:
    """Remove all handlers from the droidpilot logger."""
    logger = logging.getLogger("droidpilot")
    logger.handlers.clear()
    logger.setLevel(logging.WARNING)


class TestSetupLogging:
    """Tests for the _setup_logging helper."""

    def teardown_method(self) -> None:
        _reset_logger()

    def test_default_level_is_info(self) -> None:
        _setup_logging()
        logger = logging.getLogger("droidpilot")
        assert logger.level == logging.INFO

    def test_verbose_sets_debug(self) -> None:
        _setup_logging(verbose=True)
        logger = logging.getLogger("droidpilot")
        assert logger.level == logging.DEBUG

    def test_quiet_sets_warning(self) -> None:
        _setup_logging(quiet=True)
        logger = logging.getLogger("droidpilot")
        assert logger.level == logging.WARNING

    def test_handler_streams_to_stderr(self) -> None:
        _setup_logging()
        logger = logging.getLogger("droidpilot")
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_verbose_format_includes_timestamp(self) -> None:
        _setup_logging(verbose=True)
        logger = logging.getLogger("droidpilot")
        formatter = logger.handlers[0].formatter
        assert formatter is not None
        assert formatter._fmt is not None and "asctime" in formatter._fmt

    def test_agent_logger_is_child(self) -> None:
        """agent.py's logger should inherit from the droidpilot logger."""
        from droidpilot.agent import logger as agent_logger

        assert agent_logger.name == "droidpilot"
