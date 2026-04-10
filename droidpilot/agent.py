import json
import logging
import time
from typing import Any

from openai import OpenAI

from . import adb
from .ui_tree import parse
from .actions import TOOLS
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger("droidpilot")

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


def run(prompt: str, model: str = "gpt-4o", max_steps: int = 30) -> str:
    client = OpenAI()

    serial = adb.check_device()
    screen_size = adb.get_screen_size()
    logger.info("Connected to device: %s", serial)
    logger.info("Screen size: %sx%s", screen_size[0], screen_size[1])
    logger.info("Task: %s", prompt)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {prompt}"},
    ]

    for step in range(1, max_steps + 1):
        try:
            tree_text, ref_map = _get_ui_tree()
        except Exception as e:
            logger.warning("Failed to read UI: %s", e)
            time.sleep(2)
            continue

        messages.append(
            {
                "role": "user",
                "content": f"Current screen UI tree:\n```\n{tree_text}\n```",
            }
        )

        response = client.chat.completions.create(  # type: ignore[call-overload]
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="required",
        )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            logger.warning("No action returned, retrying...")
            continue

        tool_call = message.tool_calls[0]
        action_name = tool_call.function.name
        action_args = json.loads(tool_call.function.arguments)

        logger.info("Step %d: %s(%s)", step, action_name, json.dumps(action_args))

        if action_name == "done":
            summary = action_args.get("summary", "Task completed.")
            logger.info("Done: %s", summary)
            return summary

        result = _execute_action(action_name, action_args, ref_map, screen_size)
        logger.debug("→ %s", result)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result or "",
            }
        )

        time.sleep(UI_SETTLE_DELAY)

    return "Max steps reached without completing the task."
