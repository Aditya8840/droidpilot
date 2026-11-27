"""MCP server exposing DroidPilot's device actions, so any MCP client (Claude, etc.) can drive the phone."""
import io

from mcp.server.fastmcp import FastMCP, Image

from . import adb
from .agent import _execute_action, _get_ui_tree

mcp = FastMCP("droidpilot")
_state: dict = {"refs": {}, "size": None}


def _act(name: str, **args) -> str:
    if _state["size"] is None:
        adb.check_device()
        _state["size"] = adb.get_screen_size()
    return _execute_action(name, args, _state["refs"], _state["size"]) or "ok"


@mcp.tool()
def read_screen() -> str:
    """Read the current screen's accessibility tree. Elements get ref IDs like [3] for tap/type_text.
    Call again after any action: refs change when the screen changes."""
    tree, _state["refs"] = _get_ui_tree()
    return tree


@mcp.tool()
def screenshot(max_width: int = 720) -> Image:
    """Screenshot of the phone (downscaled JPEG). Use when the tree lacks visual info, e.g. photos."""
    from PIL import Image as PILImage

    img = PILImage.open(io.BytesIO(adb.screenshot())).convert("RGB")
    if img.width > max_width:
        img = img.resize((max_width, img.height * max_width // img.width))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=80)
    return Image(data=buf.getvalue(), format="jpeg")


@mcp.tool()
def tap(ref: int) -> str:
    """Tap the element with this ref from the last read_screen."""
    return _act("tap", ref=ref)


@mcp.tool()
def type_text(ref: int, text: str) -> str:
    """Focus the field with this ref and type ASCII text."""
    return _act("type_text", ref=ref, text=text)


@mcp.tool()
def swipe(direction: str) -> str:
    """Swipe up (reveals content below), down, left or right."""
    return _act("swipe", direction=direction)


@mcp.tool()
def press(key: str) -> str:
    """Press a key: back, home or enter."""
    return _act(f"press_{key}")


@mcp.tool()
def open_app(package_name: str) -> str:
    """Launch an app by package name."""
    return _act("open_app", package_name=package_name)


@mcp.tool()
def list_apps(name: str = "") -> str:
    """List installed packages, optionally filtered by substring."""
    return _act("list_apps", name=name)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
