import re
from lxml import etree

SKIP_CONTAINERS = {"FrameLayout", "LinearLayout", "RelativeLayout", "View"}


def _parse_bounds(bounds_str: str) -> tuple[int, int, int, int] | None:
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    if not match:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        int(match.group(4)),
    )


def _center_of_bounds(bounds: tuple[int, int, int, int]) -> tuple[int, int]:
    left, top, right, bottom = bounds
    return (left + right) // 2, (top + bottom) // 2


def _short_class_name(full_class: str) -> str:
    if "." in full_class:
        return full_class.rsplit(".", 1)[1]
    return full_class


def _is_visible(bounds: tuple[int, int, int, int] | None) -> bool:
    if bounds is None:
        return False
    left, top, right, bottom = bounds
    return (right - left) > 0 and (bottom - top) > 0


def _build_flags(node: etree._Element) -> list[str]:
    flags = []
    clickable = node.get("clickable") == "true"
    scrollable = node.get("scrollable") == "true"
    checkable = node.get("checkable") == "true"
    checked = node.get("checked") == "true"
    focusable = node.get("focusable") == "true"
    enabled = node.get("enabled") == "true"

    if clickable:
        flags.append("clickable")
    if scrollable:
        flags.append("scrollable")
    if checkable and checked:
        flags.append("checked")
    elif checkable:
        flags.append("unchecked")
    if focusable:
        flags.append("focusable")
    if not enabled:
        flags.append("disabled")

    return flags


def _build_element_line(ref_id: int, node: etree._Element, depth: int) -> str:
    class_name = _short_class_name(node.get("class", ""))
    text = node.get("text", "").strip()
    content_desc = node.get("content-desc", "").strip()
    resource_id = node.get("resource-id", "").strip()

    indent = "  " * depth
    parts = [f"[{ref_id}]", class_name]

    if text:
        parts.append(f'"{text}"')
    if content_desc:
        parts.append(f'(desc: "{content_desc}")')

    flags = _build_flags(node)
    if flags:
        parts.append(f"({', '.join(flags)})")

    if resource_id:
        short_id = resource_id.rsplit("/", 1)[-1] if "/" in resource_id else resource_id
        parts.append(f"[id: {short_id}]")

    return f"{indent}{' '.join(parts)}"


def _has_meaningful_info(node: etree._Element) -> bool:
    text = node.get("text", "").strip()
    content_desc = node.get("content-desc", "").strip()
    clickable = node.get("clickable") == "true"
    scrollable = node.get("scrollable") == "true"
    checkable = node.get("checkable") == "true"
    return bool(text or content_desc or clickable or scrollable or checkable)


def parse(xml_str: str) -> tuple[str, dict[int, tuple[int, int]]]:
    root = etree.fromstring(xml_str.encode("utf-8"))
    lines: list[str] = []
    ref_map: dict[int, tuple[int, int]] = {}
    ref_counter = [0]

    def _walk(node: etree._Element, depth: int = 0) -> None:
        bounds = _parse_bounds(node.get("bounds", ""))
        if not _is_visible(bounds):
            return

        class_name = _short_class_name(node.get("class", ""))

        if not _has_meaningful_info(node) and class_name in SKIP_CONTAINERS:
            for child in node:
                _walk(child, depth)
            return

        ref_counter[0] += 1
        ref_id = ref_counter[0]
        assert bounds is not None  # guaranteed by _is_visible check above
        ref_map[ref_id] = _center_of_bounds(bounds)
        lines.append(_build_element_line(ref_id, node, depth))

        for child in node:
            _walk(child, depth + 1)

    for child in root:
        _walk(child, depth=0)

    return "\n".join(lines), ref_map
