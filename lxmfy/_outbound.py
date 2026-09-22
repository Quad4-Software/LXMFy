"""Outbound message delivery for LXMFBot."""

import time
from queue import Full
from types import SimpleNamespace
from typing import Any, cast

import RNS
from LXMF import LXMessage

from .attachments import Attachment, pack_attachment
from .signatures import sign_outgoing_message


class _PendingSendAnnounceHandler:
    """Retries deferred outbound messages when their destination announces."""

    aspect_filter = "lxmf.delivery"

    def __init__(self, bot):
        self.bot = bot

    def received_announce(self, destination_hash, announced_identity, app_data):
        self.bot._flush_pending_sends(
            RNS.hexrep(destination_hash, delimit=False),
        )


class OutboundMixin:
    """Outbound queueing, delivery retries, and persistence."""

    def send(
        self,
        destination: str,
        message: str,
        title: str = "Reply",
        lxmf_fields: dict | None = None,
        stamp_cost: int | None = None,
        opportunistic: bool | None = None,
        method=None,
        include_ticket: bool | None = None,
        defer: bool | None = None,
    ):
        """Send a message to a destination, optionally with custom LXMF fields.

        Args:
            destination: The destination hash.
            message: The message content (will be utf-8 encoded).
            title: The message title (optional, will be utf-8 encoded).
            lxmf_fields: Optional dictionary of LXMF fields.
            stamp_cost: Optional outbound stamp cost for this message.
                If omitted, LXMF takes the cost from the peer announce.
                BotConfig.stamp_cost only applies to inbound delivery.
            opportunistic: Whether to use opportunistic sending (try direct, then prop).
                           If None, uses config.opportunistic_sending.
            method: Optional explicit LXMF delivery method override for crash recovery.
            include_ticket: Whether to include an LXMF reply ticket.
                If None, uses BotConfig.include_tickets (default True).
            defer: When the destination identity is unknown, hold the message
                and retry after its next announce instead of dropping it.
                If None, uses BotConfig.pending_sends_enabled (default True).

        """
        if self.config.test_mode:
            # In test mode, just queue a mock message
            mock_message = SimpleNamespace()
            try:
                mock_message.destination_hash = bytes.fromhex(destination)
            except ValueError:
                mock_message.destination_hash = destination.encode("utf-8")
            mock_message.content = message.encode("utf-8")
            mock_message.title = title.encode("utf-8") if title else None
            mock_message.fields = lxmf_fields
            mock_message.desired_method = method
            mock_message.include_ticket = (
                self.config.include_tickets
                if include_ticket is None
                else include_ticket
            )
            mock_message.stamp_cost = stamp_cost
            return self._enqueue_outbound(mock_message)

        try:
            dest_hash_bytes = bytes.fromhex(destination)
        except ValueError:
            RNS.log(f"Invalid destination hash format: {destination}", RNS.LOG_ERROR)
            return False

        if len(dest_hash_bytes) != RNS.Reticulum.TRUNCATED_HASHLENGTH // 8:
            RNS.log(f"Invalid destination hash length for {destination}", RNS.LOG_ERROR)
            return False

        identity_instance = RNS.Identity.recall(dest_hash_bytes)
        if identity_instance is None:
            RNS.log(
                f"Could not recall an Identity for {destination}. Requesting path...",
                RNS.LOG_WARNING,
            )
            RNS.Transport.request_path(dest_hash_bytes)
            should_defer = self.config.pending_sends_enabled if defer is None else defer
            if should_defer:
                self._defer_pending_send(
                    destination,
                    message,
                    title,
                    lxmf_fields,
                    stamp_cost,
                    method,
                    include_ticket,
                )
                RNS.log(
                    f"Message for {destination} held until its identity is learned",
                    RNS.LOG_INFO,
                )
                return True
            RNS.log(
                "Path requested. If the network knows a path, you will receive an announce shortly.",
                RNS.LOG_INFO,
            )
            return False
        lxmf_destination_obj = RNS.Destination(
            identity_instance,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            "lxmf",
            "delivery",
        )

        # Ensure message and title are bytes
        message_bytes = message.encode("utf-8")
        title_bytes = title.encode("utf-8") if title else None

        # Determine delivery method based on retry count
        attempts = self.delivery_attempts.get(destination, 0)
        max_retries = self.config.direct_delivery_retries

        # Check if we should prefer propagation
        has_prop_node = (
            self.config.propagation_node
            or self.config.autopeer_propagation
            or (
                self.router.get_outbound_propagation_node() is not None
                if self.router
                else False
            )
        )

        is_opportunistic = (
            opportunistic
            if opportunistic is not None
            else self.config.opportunistic_sending
        )

        if attempts >= max_retries and self.config.propagation_fallback_enabled:
            if not has_prop_node and not self.config.enable_propagation_node:
                RNS.log(
                    f"Propagation fallback triggered for {destination}, but no propagation_node configured, "
                    "autopeer disabled, and bot is not a propagation node. Message will likely fail. "
                    "Configure propagation_node, enable autopeer_propagation, run as propagation node, "
                    "or disable propagation_fallback_enabled.",
                    RNS.LOG_ERROR,
                )
            desired_method = LXMessage.PROPAGATED
            RNS.log(
                f"Using propagation for {destination} after {attempts} failed direct attempts",
                RNS.LOG_INFO,
            )
        elif is_opportunistic:
            # Packet delivery without requiring a Link first. Works much more
            # reliably through public TCP/backbone entrypoints than DIRECT.
            desired_method = LXMessage.OPPORTUNISTIC
            peer_ratchet = RNS.Identity.current_ratchet_id(dest_hash_bytes)
            if peer_ratchet is None:
                RNS.log(
                    f"No known ratchet for {destination}. "
                    "Opportunistic delivery will use static identity encryption "
                    "until a peer announce arrives.",
                    RNS.LOG_DEBUG,
                )
        else:
            desired_method = LXMessage.DIRECT

        if method is not None:
            desired_method = method

        # Use the peer stamp cost from LXMF unless the caller overrides it.
        # BotConfig.stamp_cost is only for inbound delivery identity setup.
        do_include_ticket = (
            self.config.include_tickets if include_ticket is None else include_ticket
        )

        lxm = LXMessage(
            lxmf_destination_obj,
            self.local,
            cast("Any", message_bytes),
            title=cast("Any", title_bytes),
            desired_method=desired_method,
            fields=lxmf_fields,
            stamp_cost=stamp_cost,
            include_ticket=do_include_ticket,
        )

        # Register callbacks to reset counter on success or track failure
        def on_delivery_success(_message):
            with self._delivery_lock:
                if destination in self.delivery_attempts:
                    self.delivery_attempts[destination] = 0
                    self._save_delivery_attempts()
                    RNS.log(
                        f"Delivery successful to {destination}, reset retry counter",
                        RNS.LOG_DEBUG,
                    )

        def on_delivery_failure(_message):
            with self._delivery_lock:
                current_attempts = self.delivery_attempts.get(destination, 0)
                self.delivery_attempts[destination] = current_attempts + 1
                self._save_delivery_attempts()

            if current_attempts + 1 < max_retries:
                RNS.log(
                    f"Delivery failed to {destination}, attempt {current_attempts + 1}/{max_retries}",
                    RNS.LOG_WARNING,
                )
            else:
                RNS.log(
                    f"Delivery failed to {destination} after {current_attempts + 1} attempts",
                    RNS.LOG_ERROR,
                )

        lxm.register_delivery_callback(on_delivery_success)
        lxm.register_failed_callback(on_delivery_failure)

        # Sign the message (pass-through for LXMF's built-in signing)
        lxm = sign_outgoing_message(self, lxm)

        # Set propagation fallback if enabled. Applies when starting with
        # opportunistic or direct delivery and a propagation node is known.
        if (
            desired_method in (LXMessage.DIRECT, LXMessage.OPPORTUNISTIC)
            and (self.config.propagation_fallback_enabled or is_opportunistic)
            and has_prop_node
        ):
            # LXMF sets try_propagation_on_fail dynamically at runtime
            lxm.try_propagation_on_fail = True

        if not self._enqueue_outbound(lxm):
            RNS.log(
                f"Failed to queue message for {destination}: outbound queue full",
                RNS.LOG_ERROR,
            )
            return False
        RNS.log(
            f"Message queued for {destination} (method: {desired_method}, opportunistic: {is_opportunistic})",
            RNS.LOG_DEBUG,
        )
        return True

    @staticmethod
    def _destination_hash_len() -> int:
        return RNS.Reticulum.TRUNCATED_HASHLENGTH // 8

    def _is_valid_destination_hex(self, destination: str) -> bool:
        if not isinstance(destination, str) or not destination:
            return False
        try:
            raw = bytes.fromhex(destination)
        except ValueError:
            return False
        return len(raw) == self._destination_hash_len()

    def _enqueue_outbound(self, lxm) -> bool:
        """Enqueue an outbound message without blocking. Drops oldest if full."""
        try:
            self.queue.put_nowait(lxm)
        except Full:
            try:
                dropped = self.queue.get_nowait()
                self.logger.warning(
                    "Outbound queue full (max=%s), dropped oldest message",
                    self.queue.maxsize,
                )
                del dropped
                self.queue.put_nowait(lxm)
            except Exception as e:
                self.logger.error("Failed to enqueue outbound message: %s", e)
                return False
        self._persist_queue()
        return True

    def _persist_queue(self):
        """Persist the outgoing message queue to storage."""
        if getattr(self.config, "message_persistence_enabled", False) is not True:
            return

        max_items = max(1, int(self.queue.maxsize or 50))
        max_content = 65536
        queued_messages = []
        with self.queue.mutex:
            snapshot = list(self.queue.queue)
        for lxm in snapshot:
            if len(queued_messages) >= max_items:
                break
            try:
                destination = RNS.hexrep(lxm.destination_hash, delimit=False)
                if not self._is_valid_destination_hex(destination):
                    self.logger.warning(
                        "Skipping persist for invalid destination hash length: %s",
                        destination,
                    )
                    continue
                content = (
                    lxm.content.decode("utf-8")
                    if isinstance(lxm.content, bytes)
                    else lxm.content
                )
                if (
                    isinstance(content, str)
                    and len(content.encode("utf-8")) > max_content
                ):
                    self.logger.warning(
                        "Skipping persist for oversized message to %s",
                        destination,
                    )
                    continue
                msg_data = {
                    "destination": destination,
                    "content": content,
                    "title": lxm.title.decode("utf-8")
                    if isinstance(lxm.title, bytes)
                    else lxm.title,
                    "fields": lxm.fields,
                    "method": lxm.desired_method,
                }
                queued_messages.append(msg_data)
            except Exception as e:
                self.logger.error("Failed to serialize message for persistence: %s", e)

        self.storage.set("persisted_queue", queued_messages)

    def _load_persisted_queue(self):
        """Load persisted messages back into the queue."""
        if getattr(self.config, "message_persistence_enabled", False) is not True:
            return

        persisted = self.storage.get("persisted_queue", [])
        if not persisted:
            return
        if not isinstance(persisted, list):
            self.storage.set("persisted_queue", [])
            return

        max_items = max(1, int(self.queue.maxsize or 50))
        if len(persisted) > max_items:
            self.logger.warning(
                "Truncating persisted queue from %s to %s messages",
                len(persisted),
                max_items,
            )
            persisted = persisted[-max_items:]

        RNS.log(f"Restoring {len(persisted)} messages from persistence", RNS.LOG_INFO)
        deferred = []
        for msg_data in persisted:
            if not isinstance(msg_data, dict):
                continue
            destination = msg_data.get("destination")
            if not isinstance(destination, str) or not self._is_valid_destination_hex(
                destination,
            ):
                self.logger.warning(
                    "Dropping persisted message with invalid destination: %s",
                    destination,
                )
                continue
            title = msg_data.get("title")
            try:
                queued = self.send(
                    destination,
                    msg_data["content"],
                    title=title if isinstance(title, str) else "Reply",
                    lxmf_fields=msg_data.get("fields"),
                    method=msg_data.get("method"),
                )
                if not queued:
                    deferred.append(msg_data)
            except Exception as e:
                self.logger.error("Failed to restore message from persistence: %s", e)
                deferred.append(msg_data)

        # Keep successfully requeued messages on disk until outbound drain.
        self._persist_queue()
        if deferred:
            current = self.storage.get("persisted_queue", [])
            if not isinstance(current, list):
                current = []
            merged = list(current) + deferred
            if len(merged) > max_items:
                merged = merged[-max_items:]
            self.storage.set("persisted_queue", merged)

    def _defer_pending_send(
        self,
        destination: str,
        message: str,
        title,
        lxmf_fields,
        stamp_cost,
        method,
        include_ticket,
    ) -> None:
        """Hold a message whose destination identity is not yet known."""
        entry = {
            "destination": destination,
            "content": message,
            "title": title,
            "fields": lxmf_fields,
            "stamp_cost": stamp_cost,
            "method": method,
            "include_ticket": include_ticket,
            "queued_at": int(time.time()),
            "attempts": 0,
        }
        with self._delivery_lock:
            pending = self.storage.get("pending_sends", [])
            if not isinstance(pending, list):
                pending = []
            pending = [e for e in pending if isinstance(e, dict)]
            pending.append(entry)
            max_pending = max(1, int(self.config.pending_sends_max or 200))
            if len(pending) > max_pending:
                dropped = len(pending) - max_pending
                pending = pending[-max_pending:]
                self.logger.warning(
                    "Pending send backlog full, dropped %s oldest message(s)",
                    dropped,
                )
            self.storage.set("pending_sends", pending)

    def _flush_pending_sends(self, destination: str | None = None) -> None:
        """Retry held messages. When destination is set, only that hash runs."""
        if not self.config.pending_sends_enabled:
            return
        if self.config.test_mode or self.router is None:
            return

        now = int(time.time())
        ttl = max(0, int(self.config.pending_sends_ttl or 0))
        with self._delivery_lock:
            pending = self.storage.get("pending_sends", [])
            if not isinstance(pending, list) or not pending:
                return
            kept, retry = [], []
            for entry in pending:
                if not isinstance(entry, dict):
                    continue
                if ttl and now - int(entry.get("queued_at", now)) > ttl:
                    self.logger.debug(
                        "Dropping expired pending send to %s",
                        entry.get("destination"),
                    )
                    continue
                if destination is None or entry.get("destination") == destination:
                    retry.append(entry)
                else:
                    kept.append(entry)

        for entry in retry:
            dest = entry.get("destination")
            if not isinstance(dest, str) or not self._is_valid_destination_hex(
                dest,
            ):
                continue
            attempts = int(entry.get("attempts", 0)) + 1
            if attempts > 50:
                self.logger.warning(
                    "Dropping pending send to %s after %s attempts",
                    dest,
                    attempts,
                )
                continue
            entry["attempts"] = attempts
            if self.send(
                dest,
                entry.get("content") or "",
                title=entry.get("title") or "Reply",
                lxmf_fields=entry.get("fields"),
                stamp_cost=entry.get("stamp_cost"),
                method=entry.get("method"),
                include_ticket=entry.get("include_ticket"),
                defer=False,
            ):
                self.logger.debug(
                    "Pending send to %s dispatched",
                    dest,
                )
            else:
                kept.append(entry)

        with self._delivery_lock:
            self.storage.set("pending_sends", kept)

    def send_with_attachment(
        self,
        destination: str,
        message: str,
        attachment: Attachment,
        title: str = "Reply",
        stamp_cost: int | None = None,
        opportunistic: bool | None = None,
        include_ticket: bool | None = None,
    ):
        """Send a message with an attachment to a destination.

        Args:
            destination: The destination hash.
            message: The message content.
            attachment: The attachment to send.
            title: The message title.
            stamp_cost: Optional outbound stamp cost for this message.
            opportunistic: Whether to use opportunistic sending.
            include_ticket: Whether to include an LXMF reply ticket.

        """
        attachment_specific_fields = pack_attachment(attachment)
        self.send(
            destination,
            message,
            title=title,
            lxmf_fields=attachment_specific_fields,
            stamp_cost=stamp_cost,
            opportunistic=opportunistic,
            include_ticket=include_ticket,
        )

    def _load_delivery_attempts(self):
        """Load delivery attempts from storage."""
        self.delivery_attempts = self.storage.get("delivery_attempts", {})

    def _save_delivery_attempts(self):
        """Save delivery attempts to storage."""
        self.storage.set("delivery_attempts", self.delivery_attempts)

    def _reset_delivery_attempts(self, destination: str):
        """Reset delivery attempts for a destination when they come back online.

        Args:
            destination: The destination hash.

        """
        with self._delivery_lock:
            if (
                destination in self.delivery_attempts
                and self.delivery_attempts[destination] > 0
            ):
                self.delivery_attempts[destination] = 0
                self._save_delivery_attempts()
                RNS.log(
                    f"Reset delivery attempts for {destination} (user came back online)",
                    RNS.LOG_DEBUG,
                )
