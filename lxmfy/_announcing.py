"""Delivery announce handling for LXMFBot."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import RNS

if TYPE_CHECKING:
    import logging

    from .config import BotConfig

BOT_DISPLAY_NAME_FILE = "bot_display_name.txt"


class AnnounceMixin:
    """Display name resolution and LXMF delivery announces."""

    config: BotConfig
    config_path: str
    local: RNS.Destination | None
    logger: logging.Logger
    announce_enabled: bool
    announce_time: int

    @property
    def name(self) -> str:
        """Bot display name used for LXMF when no file override applies."""
        return self.config.name

    @name.setter
    def name(self, value: str) -> None:
        self.config.name = value
        self._sync_delivery_display_name()

    def _effective_announce_display_name(self) -> str:
        """Resolve the display name for lxmf/delivery announce app_data."""
        if self.config.announce_display_name_file:
            path = os.path.join(
                self.config_path,
                self.config.announce_display_name_file,
            )
            if os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        text = f.read().strip()
                    if text:
                        return text
                except OSError:
                    pass

        default_path = os.path.join(self.config_path, BOT_DISPLAY_NAME_FILE)
        if os.path.isfile(default_path):
            try:
                with open(default_path, encoding="utf-8") as f:
                    text = f.read().strip()
                if text:
                    return text
            except OSError:
                pass

        return self.config.name or "LXMFBot"

    def _sync_delivery_display_name(self) -> None:
        if not self.local:
            return
        # RNS Destination.display_name is set dynamically at runtime
        setattr(  # noqa: B010 - direct assignment is untyped on Destination
            self.local,
            "display_name",
            self._effective_announce_display_name(),
        )

    def announce_now(self, force: bool = False) -> None:
        """Send an LXMF delivery announce using the current display name.

        LXMF builds delivery announce app_data from the destination display name
        at announce time; this method refreshes that from :attr:`name`, optional
        ``announce_display_name_file``, or ``bot_display_name.txt`` before
        sending.

        Args:
            force: If True, send now and skip the on-disk announce interval
                throttle (still respects ``announce_enabled`` and requires a
                running router). If False, behave like the periodic announce
                task (honours ``announce_time`` and the throttle file).

        """
        if self.config.test_mode or not self.local:
            RNS.log("Announce skipped (test mode or no router)", RNS.LOG_DEBUG)
            return
        if not self.announce_enabled:
            RNS.log("Announcements disabled", RNS.LOG_DEBUG)
            return
        if not force and self.announce_time == 0:
            RNS.log("Announcements disabled", RNS.LOG_DEBUG)
            return

        announce_path = os.path.join(self.config_path, "announce")
        if not force:
            if os.path.isfile(announce_path):
                with open(announce_path) as f:
                    try:
                        announce = int(f.readline())
                    except ValueError:
                        announce = 0
            else:
                announce = 0

            if announce > int(time.time()):
                RNS.log("Recent announcement", RNS.LOG_DEBUG)
                return

        self._sync_delivery_display_name()
        self.local.announce()

        try:
            with open(announce_path, "w+") as af:
                interval = max(0, self.announce_time)
                af.write(str(int(time.time()) + interval))
        except OSError as e:
            self.logger.warning("Could not write announce throttle file: %s", e)

        RNS.log(
            f"Announcement sent, next announce in {self.announce_time} seconds",
            RNS.LOG_INFO,
        )
