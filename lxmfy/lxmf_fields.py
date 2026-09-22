"""LXMF field constants and helpers for structured commands and results."""

try:
    from LXMF.LXMF import FIELD_COMMANDS as _fc
    from LXMF.LXMF import FIELD_RESULTS as _fr
except ImportError:
    _fc = 0x09
    _fr = 0x0A

FIELD_COMMANDS: int = _fc
FIELD_RESULTS: int = _fr


def unpack_commands(fields: dict | None) -> list[dict]:
    """Extract command entries from LXMF message fields.

    Supports ``FIELD_COMMANDS`` being a single dict or a list of dicts.
    Each dict should contain at least a ``command`` or ``cmd`` key.

    Args:
        fields: The ``fields`` dict from an :class:`LXMF.LXMessage`.

    Returns:
        A list of command dicts.

    """
    if not fields:
        return []

    raw = fields.get(FIELD_COMMANDS)
    if raw is None:
        return []

    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [entry for entry in raw if isinstance(entry, dict)]

    return []


def pack_result(result, request_id: str | None = None, status: str = "ok") -> dict:
    """Pack a result into a ``FIELD_RESULTS``-compatible dict.

    Args:
        result: The result payload (any serialisable value).
        request_id: Optional correlation ID from the original request.
        status: Status string, e.g. ``"ok"`` or ``"error"``.

    Returns:
        A dict suitable for ``FIELD_RESULTS``.

    """
    data = {"result": result, "status": status}
    if request_id is not None:
        data["request_id"] = request_id
    return data
