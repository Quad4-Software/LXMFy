"""Inbound message pipeline for LXMFBot."""

from types import SimpleNamespace
from typing import TYPE_CHECKING

import RNS

from ._sync import run_sync
from .events import Event, EventPriority
from .lxmf_fields import FIELD_RESULTS, pack_result, unpack_commands
from .middleware import MiddlewareContext, MiddlewareType
from .permissions import DefaultPerms
from .signatures import verify_incoming_message

if TYPE_CHECKING:
    from .core import LXMFBot


class InboundMixin:
    """Message intake, dispatch, and handler registration."""

    def _register_builtin_events(self: "LXMFBot"):
        """Register built-in event handlers."""

        @self.events.on("message_received", EventPriority.HIGHEST)
        def handle_message(event):
            """Handles incoming messages, performing spam checks."""
            sender = event.data["sender"]
            if not self.permissions.has_permission(sender, DefaultPerms.BYPASS_SPAM):
                allowed, msg = self.spam_protection.check_spam(sender)
                if not allowed:
                    event.cancel()
                    if msg:
                        self.send(sender, msg)
                    return

            self._reset_delivery_attempts(sender)

    def _process_message(self: "LXMFBot", message, sender):
        """Process an incoming message."""
        try:
            content = message.content.decode("utf-8") if message.content else ""
            receipt = RNS.hexrep(message.hash, delimit=False)
            msg_fields = getattr(message, "fields", None) or {}

            field_commands = unpack_commands(msg_fields)
            request_id = None
            if field_commands:
                request_id = field_commands[0].get("request_id")
            has_field_commands = bool(field_commands)

            def reply(response, **kwargs):
                """Helper function to reply to a message."""
                lxmf_fields = kwargs.pop("lxmf_fields", None) or {}
                if has_field_commands or request_id is not None:
                    lxmf_fields[FIELD_RESULTS] = pack_result(
                        response,
                        request_id,
                        kwargs.pop("status", "ok"),
                    )
                if lxmf_fields:
                    kwargs["lxmf_fields"] = lxmf_fields
                self.send(sender, response, **kwargs)

            if self.config.first_message_enabled:
                is_first = False
                with self._receive_lock:
                    first_messages = self.storage.get("first_messages", {})
                    if not isinstance(first_messages, dict):
                        first_messages = {}
                    if sender not in first_messages:
                        is_first = True
                        first_messages[sender] = True
                        while len(first_messages) > 10000:
                            first_messages.pop(next(iter(first_messages)))
                        self.storage.set("first_messages", first_messages)
                if is_first:
                    self.logger.debug("First message from %s", sender)
                    for handler in self.first_message_handlers:
                        if run_sync(handler, sender, message):
                            self.logger.debug(
                                "First message from %s consumed by handler",
                                sender,
                            )
                            return

            if not self.permissions.has_permission(sender, DefaultPerms.USE_BOT):
                self.logger.debug("Message from %s denied by permissions", sender)
                return

            # Call message handlers
            for handler in self.message_handlers:
                if run_sync(handler, sender, message):
                    self.logger.debug(
                        "Message from %s consumed by message handler",
                        sender,
                    )
                    return

            msg_ctx = {
                "lxmf": message,
                "reply": reply,
                "sender": sender,
                "content": content,
                "hash": receipt,
                "fields": msg_fields,
                "request_id": request_id,
            }
            msg = SimpleNamespace(**msg_ctx)

            ctx = MiddlewareContext(MiddlewareType.PRE_COMMAND, msg)
            if self.middleware.execute(MiddlewareType.PRE_COMMAND, ctx) is None:
                return

            # Process structured commands from LXMF fields
            if getattr(self.config, "lxmf_commands_enabled", True) and field_commands:
                for cmd_data in field_commands:
                    cmd_name = cmd_data.get("command") or cmd_data.get("cmd")
                    cmd_args = cmd_data.get("args", [])
                    if isinstance(cmd_args, str):
                        cmd_args = [cmd_args]
                    if not isinstance(cmd_args, list):
                        cmd_args = []
                    if cmd_name and self._execute_command(cmd_name, cmd_args, msg):
                        return
                    reply(f"Unknown command: {cmd_name}", status="error")
                    return

            parts = content.split()
            if parts and (
                self.command_prefix is None or content.startswith(self.command_prefix)
            ):
                command_name = (
                    parts[0][len(self.command_prefix) :]
                    if self.command_prefix
                    else parts[0]
                )
                args = parts[1:]
                self.logger.debug(
                    "Dispatching command %s for %s",
                    command_name,
                    sender,
                )
                if self._execute_command(command_name, args, msg):
                    return

            # NLP Intent matching
            if self.config.nlp_enabled:
                intent_name, score = self.nlp.predict(content)
                if intent_name and intent_name in self.intents:
                    self.logger.debug(
                        "NLP Intent Matched: %s (score: %.2f)",
                        intent_name,
                        score,
                    )
                    msg.intent = intent_name
                    msg.intent_score = score
                    try:
                        run_sync(self.intents[intent_name], msg)
                        return
                    except Exception:
                        self.logger.exception(
                            "Error executing intent %s",
                            intent_name,
                        )

            for callback in self.delivery_callbacks:
                run_sync(callback, msg)

        except Exception:
            self.logger.exception("Error processing message from %s", sender)

    def _message_received(self: "LXMFBot", message):
        """Handle received messages."""
        try:
            sender = RNS.hexrep(message.source_hash, delimit=False)
            receipt = RNS.hexrep(message.hash, delimit=False)

            with self._receive_lock:
                if receipt in self.receipts:
                    self.logger.debug(
                        "Duplicate delivery of %s from %s ignored",
                        receipt,
                        sender,
                    )
                    return
                self.receipts.append(receipt)
                if len(self.receipts) > 100:
                    del self.receipts[:-100]

            self.logger.debug("Message %s received from %s", receipt, sender)

            event_data = {
                "message": message,
                "sender": sender,
                "receipt": receipt,
            }

            ctx = MiddlewareContext(MiddlewareType.PRE_EVENT, event_data)
            if self.middleware.execute(MiddlewareType.PRE_EVENT, ctx) is None:
                return

            event = Event("message_received", event_data)
            self.events.dispatch(event)

            if not event.cancelled:
                # Verify message signature if enabled
                if verify_incoming_message(self, message, sender):
                    self._process_message(message, sender)
                else:
                    RNS.log(
                        f"Rejected message from {sender} due to invalid signature",
                        RNS.LOG_WARNING,
                    )

        except Exception:
            self.logger.exception("Error handling received message")

    def received(self: "LXMFBot", function):
        """Decorator for registering delivery callbacks.

        Args:
            function: The function to call when a message is delivered.

        """
        self.delivery_callbacks.append(function)
        return function

    def intent(self: "LXMFBot", name: str, examples: list[str]):
        """Decorator for registering intent handlers.

        Args:
            name: The name of the intent.
            examples: A list of example phrases for this intent.

        """

        def decorator(func):
            self.nlp.add_intent(name, examples)
            self.intents[name] = func
            return func

        return decorator

    def on_first_message(self: "LXMFBot"):
        """Decorator for registering first message handlers"""

        def decorator(func):
            """Registers a function to be called on the first message from a sender."""
            self.first_message_handlers.append(func)
            return func

        return decorator

    def on_message(self: "LXMFBot"):
        """Decorator for registering message handlers"""

        def decorator(func):
            """Registers a function to be called on every message."""
            self.message_handlers.append(func)
            return func

        return decorator
