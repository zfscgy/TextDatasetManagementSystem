"""Column renaming/mapping for dataset rows."""


def parse_mapping(spec: str) -> tuple[list[str], list[str]]:
    """
    Parse a mapping spec like 'old:new' or 'messages.from:messages.role'.
    Returns (src_parts, dst_parts) where each is a list of path segments.
    Raises ValueError if the spec is malformed.
    """
    if ":" not in spec:
        raise ValueError(f"Invalid column mapping '{spec}': expected 'src:dst' format")
    src, _, dst = spec.partition(":")
    src_parts = [s for s in src.split(".") if s]
    dst_parts = [s for s in dst.split(".") if s]
    if not src_parts or not dst_parts:
        raise ValueError(f"Invalid column mapping '{spec}': src and dst must be non-empty")
    return src_parts, dst_parts


def _rename_in(obj, src: list[str], dst: list[str]) -> None:
    """
    In-place rename of a nested key in obj.
    When a list is encountered while traversing the path, the rename is applied
    to every dict item in that list.
    """
    if not isinstance(obj, dict):
        return

    if len(src) == 1:
        # Leaf rename
        src_key, dst_key = src[0], dst[0]
        if src_key in obj and src_key != dst_key:
            obj[dst_key] = obj.pop(src_key)
        return

    # Navigate one level deeper
    key = src[0]
    if key not in obj:
        return

    child = obj[key]
    if isinstance(child, list):
        for item in child:
            _rename_in(item, src[1:], dst[1:])
    elif isinstance(child, dict):
        _rename_in(child, src[1:], dst[1:])


def apply_mappings(obj: dict, mappings: list[tuple[list[str], list[str]]]) -> dict:
    """
    Apply a list of (src_parts, dst_parts) renames to obj in order.
    Returns the same dict (mutated in-place).
    """
    for src_parts, dst_parts in mappings:
        _rename_in(obj, src_parts, dst_parts)
    return obj
