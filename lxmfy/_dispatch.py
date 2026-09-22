"""Command registration and execution for LXMFBot."""

import inspect

from .commands import Command
from .middleware import MiddlewareType


class DispatchMixin:
    """Command decorator, admin check, and command execution."""

    def command(self, *args, **kwargs):
        """Decorator for registering commands.

        Args:
            *args: Command name (optional).
            **kwargs: Command attributes (name, description, admin_only).

        """

        def decorator(func):
            """The actual decorator that registers the command."""
            name = args[0] if len(args) > 0 else kwargs.get("name", func.__name__)

            description = kwargs.get("description", "No description provided")
            admin_only = kwargs.get("admin_only", False)

            cmd = Command(name=name, description=description, admin_only=admin_only)
            cmd.callback = func
            self.commands[name] = cmd
            return func

        return decorator

    def is_admin(self, sender):
        """Check if a sender is an admin.

        Args:
            sender: The sender's identity hash.

        Returns:
            True if the sender is an admin, False otherwise.

        """
        return sender in self.admins

    def _execute_command(self, cmd_name: str, args: list, msg) -> bool:
        """Execute a registered command by name.

        Returns:
            True if the command was found and executed (or raised an error),
            False if no command with that name exists.

        """
        if cmd_name not in self.commands:
            return False

        cmd = self.commands[cmd_name]

        if not self.permissions.has_permission(msg.sender, cmd.permissions):
            self.send(msg.sender, "You don't have permission to use this command.")
            return True

        try:
            sig = inspect.signature(cmd.callback)
            params = list(sig.parameters.values())

            converted_args = []
            for i, arg_val in enumerate(args):
                param_idx = i + 1
                if param_idx < len(params):
                    param = params[param_idx]
                    annotation = param.annotation
                    if (
                        annotation != inspect.Parameter.empty
                        and hasattr(annotation, "__call__")
                        and not isinstance(annotation, str)
                    ):
                        try:
                            converted_args.append(annotation(arg_val))
                        except (ValueError, TypeError):
                            converted_args.append(arg_val)
                    else:
                        converted_args.append(arg_val)
                else:
                    converted_args.append(arg_val)

            msg.args = converted_args
            msg.is_admin = msg.sender in self.admins

            try:
                if cmd.threaded:
                    self.thread_pool.submit(cmd.callback, msg)
                else:
                    cmd.callback(msg)
            finally:
                self.middleware.execute(MiddlewareType.POST_COMMAND, msg)
            return True

        except Exception as e:
            self.logger.exception("Error executing command %s", cmd_name)
            self.send(msg.sender, f"Error executing command: {e}")
            return True
