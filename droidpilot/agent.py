import json
import time

from . import adb
from .ui_tree import parse
from .actions import TOOLS
from .prompts import SYSTEM_PROMPT
from .providers import create_provider

SWIPE_OFFSETS = {
    "up": (0, 1, 0, -1),
    "down": (0, -1, 0, 1),
    "left": (1, 0, -1, 0),
    "right": (-1, 0, 1, 0),
}

UI_SETTLE_DELAY = 1
TAP_TO_TYPE_DELAY = 0.3


def _get_ui_tree() -> tuple[str, dict[int, tuple[int, int]]]:
    xml = adb.dump_ui()
    return parse(xml)


def _compute_swipe_coords(
    direction: str, screen_w: int, screen_h: int
) -> tuple[int, int, int, int]:
    if direction not in SWIPE_OFFSETS:
        raise ValueError(f"Unknown swipe direction: {direction}")

    cx, cy = screen_w // 2, screen_h // 2
    dist_x, dist_y = screen_w // 3, screen_h // 3
    ox1, oy1, ox2, oy2 = SWIPE_OFFSETS[direction]

    return (
        cx + ox1 * dist_x,
        cy + oy1 * dist_y,
        cx + ox2 * dist_x,
        cy + oy2 * dist_y,
    )


def _execute_action(
    name: str,
    args: dict,
    ref_map: dict[int, tuple[int, int]],
    screen_size: tuple[int, int],
) -> str | None:
    if name == "tap":
        ref = args["ref"]
        if ref not in ref_map:
            return f"Error: ref [{ref}] not found on screen. Re-read the UI tree."
        x, y = ref_map[ref]
        adb.tap(x, y)
        return f"Tapped [{ref}] at ({x}, {y})"

    if name == "type_text":
        ref = args["ref"]
        text = args["text"]
        if ref not in ref_map:
            return f"Error: ref [{ref}] not found on screen."
        x, y = ref_map[ref]
        adb.tap(x, y)
        time.sleep(TAP_TO_TYPE_DELAY)
        adb.input_text(text)
        return f'Typed "{text}" into [{ref}]'

    if name == "swipe":
        direction = args["direction"]
        x1, y1, x2, y2 = _compute_swipe_coords(direction, *screen_size)
        adb.swipe(x1, y1, x2, y2, duration_ms=400)
        return f"Swiped {direction}"

    if name == "press_back":
        adb.press_back()
        return "Pressed back"

    if name == "press_home":
        adb.press_home()
        return "Pressed home"

    if name == "press_enter":
        adb.press_enter()
        return "Pressed enter"

    if name == "list_apps":
        name_filter = args.get("name", "")
        packages = adb.list_packages(name_filter)
        if not packages:
            return f"No apps found matching '{name_filter}'"
        return f"Found {len(packages)} app(s):\n" + "\n".join(packages)

    if name == "open_app":
        package = args["package_name"]
        adb.open_app(package)
        return f"Launched {package}"

    if name == "wait":
        seconds = min(max(args.get("seconds", 2), 1), 10)
        time.sleep(seconds)
        return f"Waited {seconds}s"

    if name == "done":
        return None

    return f"Unknown action: {name}"


def run(
    prompt: str,
    provider: str = "openai",
    model: str | None = None,
    max_steps: int = 30,
) -> str:
    llm = create_provider(provider, model, SYSTEM_PROMPT, TOOLS)

    serial = adb.check_device()
    screen_size = adb.get_screen_size()
    print(f"Connected to device: {serial}")
    print(f"Screen size: {screen_size[0]}x{screen_size[1]}")
    print(f"Task: {prompt}\n")

    llm.add_user_message(f"Task: {prompt}")

    for step in range(1, max_steps + 1):
        try:
            tree_text, ref_map = _get_ui_tree()
        except Exception as e:
            print(f"  [!] Failed to read UI: {e}")
            time.sleep(2)
            continue

        llm.add_user_message(f"Current screen UI tree:\n```\n{tree_text}\n```")

        tool_call = llm.get_tool_call()

        if not tool_call:
            print("  [!] No action returned, retrying...")
            continue

        print(f"  Step {step}: {tool_call.name}({json.dumps(tool_call.arguments)})")

        if tool_call.name == "done":
            summary = tool_call.arguments.get("summary", "Task completed.")
            print(f"\nDone: {summary}")
            return summary

        result = _execute_action(
            tool_call.name, tool_call.arguments, ref_map, screen_size
        )
        print(f"    -> {result}")

        llm.add_tool_result(result or "")

        time.sleep(UI_SETTLE_DELAY)

    return "Max steps reached without completing the task."
