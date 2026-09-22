"""Optional Landlock LSM filesystem sandbox for LXMFy (Linux only)."""

from __future__ import annotations

import logging
import os
import site
import sys
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from landlockpy import AccessFS, Ruleset

try:
    import landlockpy
    from landlockpy import AccessFS

    _READ_ACCESS = AccessFS.READ_FILE | AccessFS.READ_DIR | AccessFS.EXECUTE
    _RW_ACCESS = ~AccessFS.NONE
    _FILE_ACCESS = AccessFS.READ_FILE | AccessFS.WRITE_FILE | AccessFS.EXECUTE
except ImportError:
    landlockpy = None

logger = logging.getLogger("lxmfy.landlock")


def _landlock_env_override() -> bool | None:
    raw = os.environ.get("LXMFY_LANDLOCK")
    if raw is None:
        return None
    val = raw.strip().lower()
    if val in ("false", "0", "no", "off"):
        return False
    if val in ("true", "1", "yes", "on"):
        return True
    return None


_landlock_support_cached: bool | None = None


def landlock_kernel_supported() -> bool:
    global _landlock_support_cached
    if _landlock_support_cached is not None:
        return _landlock_support_cached
    if sys.platform != "linux" or landlockpy is None:
        _landlock_support_cached = False
        return False
    _landlock_support_cached = landlockpy.supported()
    return _landlock_support_cached


def landlock_requested(config_enabled: bool = True) -> bool:
    if sys.platform != "linux":
        return False
    override = _landlock_env_override()
    if override is False:
        return False
    if not config_enabled:
        return False
    if override is True:
        return True
    return landlock_kernel_supported()


def landlock_auto_enabled(config_enabled: bool = True) -> bool:
    return landlock_requested(config_enabled) and _landlock_env_override() is None


def landlock_disabled_by_env() -> bool:
    return _landlock_env_override() is False


def _existing_dir(path: str | None) -> str | None:
    if not path:
        return None
    resolved = os.path.abspath(os.path.expanduser(path))
    if os.path.isdir(resolved):
        return resolved
    parent = os.path.dirname(resolved)
    if parent and os.path.isdir(parent):
        return parent
    return None


def _collect_read_roots(extra_read_paths: list[str] | None = None) -> list[str]:
    roots = {
        "/usr",
        "/lib",
        "/lib64",
        "/etc",
        "/bin",
        "/sbin",
        "/proc",
    }
    for path in sys.path:
        existing = _existing_dir(path)
        if existing:
            roots.add(existing)
    for path in site.getsitepackages():
        existing = _existing_dir(path)
        if existing:
            roots.add(existing)
    user_site = site.getusersitepackages()
    existing = _existing_dir(user_site)
    if existing:
        roots.add(existing)
    for path in extra_read_paths or []:
        existing = _existing_dir(path)
        if existing:
            roots.add(existing)
    return sorted(roots)


def _collect_rw_roots(
    storage_dir: str | None,
    reticulum_config_dir: str | None,
    config_dir: str | None,
    cogs_dir: str | None,
    log_dir: str | None,
    temp_only: bool = False,
) -> list[str]:
    paths: list[str] = []
    candidates: list[str | None]
    if temp_only:
        candidates = [tempfile.gettempdir()]
    else:
        candidates = [
            storage_dir,
            reticulum_config_dir,
            config_dir,
            cogs_dir,
            log_dir,
            tempfile.gettempdir(),
            "/dev/shm",  # noqa: S108  # nosec B108
            "/run",  # nosec B108
        ]
    for candidate in candidates:
        existing = _existing_dir(candidate)
        if existing and existing not in paths:
            paths.append(existing)
    if not temp_only and os.path.isdir("/dev"):
        paths.append("/dev")
    return paths


def _allow_path(ruleset: Ruleset, path: str, access: AccessFS) -> None:
    if not path or not os.path.exists(path):
        return
    if not os.path.isdir(path):
        access &= _FILE_ACCESS
    try:
        ruleset.allow_path(path, access)
    except OSError:
        return


def apply_landlock_sandbox(
    *,
    storage_dir: str | None = None,
    reticulum_config_dir: str | None = None,
    config_dir: str | None = None,
    cogs_dir: str | None = None,
    log_dir: str | None = None,
    extra_read_paths: list[str] | None = None,
    temp_only: bool = False,
    config_enabled: bool = True,
) -> bool:
    """Apply Landlock rules. Returns True when the sandbox is active."""
    if not landlock_requested(config_enabled) or landlockpy is None:
        return False

    try:
        with landlockpy.Ruleset() as ruleset:
            for root in _collect_read_roots(extra_read_paths):
                _allow_path(ruleset, root, _READ_ACCESS)
            for root in _collect_rw_roots(
                storage_dir,
                reticulum_config_dir,
                config_dir,
                cogs_dir,
                log_dir,
                temp_only=temp_only,
            ):
                _allow_path(ruleset, root, _RW_ACCESS)
            ruleset.restrict()
    except OSError as exc:
        logger.warning("Landlock disabled: %s", exc)
        return False

    if landlock_auto_enabled(config_enabled):
        logger.info("Landlock filesystem sandbox enabled (auto-detected on Linux)")
    else:
        logger.info("Landlock filesystem sandbox enabled")
    return True


def landlock_status_dict(
    *,
    active: bool = False,
    config_enabled: bool = True,
) -> dict[str, bool]:
    """Return a dict describing Landlock availability and state."""
    return {
        "landlock_kernel_supported": landlock_kernel_supported(),
        "landlock_requested": landlock_requested(config_enabled),
        "landlock_auto_enabled": landlock_auto_enabled(config_enabled),
        "landlock_disabled_by_env": landlock_disabled_by_env(),
        "landlock_active": active,
    }
