import subprocess
import re
import shutil

SHELL_ESCAPE_CHARS = {
    " ": "%s",
    "&": "\\&",
    "<": "\\<",
    ">": "\\>",
    "(": "\\(",
    ")": "\\)",
    "|": "\\|",
    ";": "\\;",
    "'": "\\'",
    '"': '\\"',
}


def _run(args: list[str], timeout: int = 10) -> str:
    result = subprocess.run(
        ["adb"] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"adb {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def check_adb_installed() -> None:
    if shutil.which("adb") is None:
        raise RuntimeError(
            "ADB not found. Install it with: brew install android-platform-tools"
        )


def check_device() -> str:
    output = _run(["devices"])
    lines = [l for l in output.splitlines()[1:] if l.strip() and "device" in l]
    if not lines:
        raise RuntimeError(
            "No Android device found. Connect via USB and enable USB debugging."
        )
    return lines[0].split("\t")[0]


def get_screen_size() -> tuple[int, int]:
    output = _run(["shell", "wm", "size"])
    match = re.search(r"(\d+)x(\d+)", output)
    if not match:
        raise RuntimeError(f"Could not parse screen size from: {output}")
    return int(match.group(1)), int(match.group(2))


def dump_ui() -> str:
    dump_path = "/sdcard/window_dump.xml"
    _run(["shell", "uiautomator", "dump", dump_path], timeout=15)
    output = _run(["shell", "cat", dump_path], timeout=10)
    xml_end = output.rfind("</hierarchy>")
    if xml_end == -1:
        raise RuntimeError(f"No UI hierarchy found in dump output:\n{output[:500]}")
    return output[: xml_end + len("</hierarchy>")]


def tap(x: int, y: int) -> None:
    _run(["shell", "input", "tap", str(x), str(y)])


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
    _run(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)])


def input_text(text: str) -> None:
    escaped = text
    for char, replacement in SHELL_ESCAPE_CHARS.items():
        escaped = escaped.replace(char, replacement)
    _run(["shell", "input", "text", escaped])


def press_key(keycode: str) -> None:
    _run(["shell", "input", "keyevent", keycode])


def press_back() -> None:
    press_key("KEYCODE_BACK")


def press_home() -> None:
    press_key("KEYCODE_HOME")


def press_enter() -> None:
    press_key("KEYCODE_ENTER")


def open_app(package_name: str) -> None:
    _run([
        "shell", "monkey",
        "-p", package_name,
        "-c", "android.intent.category.LAUNCHER",
        "1",
    ])


def list_packages(name: str = "") -> list[str]:
    output = _run(["shell", "pm", "list", "packages"], timeout=15)
    packages = [line.replace("package:", "") for line in output.splitlines()]
    if name:
        packages = [p for p in packages if name.lower() in p.lower()]
    return sorted(packages)
