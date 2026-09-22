"""LXMF field constants and helpers for structured commands and results."""

try:
    from LXMF.LXMF import FIELD_COMMANDS as _fc
    from LXMF.LXMF import FIELD_REACTION as _frc
    from LXMF.LXMF import FIELD_RESULTS as _fr
    from LXMF.LXMF import REACTION_CONTENT as _rc
    from LXMF.LXMF import REACTION_TO as _rt
except ImportError:
    _fc = 0x09
    _fr = 0x0A
    _frc = 0x40
    _rt = 0x00
    _rc = 0x01

FIELD_COMMANDS: int = _fc
FIELD_RESULTS: int = _fr
FIELD_REACTION: int = _frc
REACTION_TO: int = _rt
REACTION_CONTENT: int = _rc

REACTION_MAX_LEN = 16


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


def _dict_key(d: dict, *keys) -> object:
    """First present key among alternatives, else None."""
    for key in keys:
        if key in d:
            return d[key]
    return None


def _hash_hex(value) -> str | None:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    if isinstance(value, str):
        h = value.strip().lower()
        if len(h) in (32, 64) and all(c in "0123456789abcdef" for c in h):
            return h
    return None


def _reaction_text(value) -> str:
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace").strip()
    elif value is None:
        text = ""
    else:
        text = str(value).strip()
    return "".join(ch for ch in text if ch.isprintable())[:REACTION_MAX_LEN]


def pack_reaction(message_hash: bytes | str, reaction: str) -> dict:
    """Build a FIELD_REACTION dict for a target message hash.

    Args:
        message_hash: The full LXMessage hash, bytes or hex string.
        reaction: The reaction content, usually a single emoji.

    """
    raw = bytes.fromhex(message_hash) if isinstance(message_hash, str) else message_hash
    return {
        FIELD_REACTION: {
            REACTION_TO: bytes(raw),
            REACTION_CONTENT: _reaction_text(reaction).encode("utf-8"),
        },
    }


def unpack_reaction(fields: dict | None, sender: str = "") -> dict | None:
    """Parse a FIELD_REACTION dict from LXMF message fields.

    Tolerates int keys, string keys, and common name variants the way
    clients like MeshChatX encode them. Returns a dict with
    reaction_to, reaction_emoji, and reaction_sender, or None when the
    fields carry no parseable reaction.
    """
    if not isinstance(fields, dict):
        return None
    raw = _dict_key(fields, FIELD_REACTION, "reaction", 0x40)
    if not isinstance(raw, dict):
        return None
    target = _dict_key(raw, REACTION_TO, 0, "0x00", "reaction_to")
    content = _dict_key(raw, REACTION_CONTENT, 1, "0x01", "reaction_content", "emoji")
    reaction_to = _hash_hex(target)
    if not reaction_to:
        return None
    return {
        "reaction_to": reaction_to,
        "reaction_emoji": _reaction_text(content),
        "reaction_sender": sender,
    }
