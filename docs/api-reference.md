# Core Components

## LXMFBot

The main bot class that handles message routing, command processing, and
bot lifecycle management.

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="MyBot",
    announce=600,
    announce_immediately=True,
    admins=set(),
    hot_reloading=False,
    rate_limit=5,
    cooldown=60,
    max_warnings=3,
    warning_timeout=300,
    command_prefix="/",
    cogs_dir="cogs",
    cogs_enabled=True,
    permissions_enabled=False,
    storage_type="json", # "json", "sqlite", or "memory"
    storage_path="data",
    first_message_enabled=True,
    event_logging_enabled=True,
    max_logged_events=1000,
    event_middleware_enabled=True,
    announce_enabled=True,
    signature_verification_enabled=False,
    require_message_signatures=False,
    identity_pinning_enabled=False,
    message_persistence_enabled=True,
    dynamic_cogs_enabled=True,
    external_cogs_enabled=True,
    external_cogs_sandbox_enabled=True,
    external_cogs_sandbox_type="auto",  # "auto", "landlock", "bwrap", "firejail", "none"
    external_cogs_timeout=30,
    landlock_enabled=True,
    nlp_enabled=False,
    nlp_threshold=0.5,
    link_support_enabled=False,
    lxmf_commands_enabled=True,
    message_queue_size=50,
    reticulum_config_dir=None,  # or LXMFY_RETICULUM_CONFIG_DIR / "~/.reticulum"
    rrc_enabled=False,
    rrc_hubs=[],
    rrc_rooms=[],
    rrc_nick=None,
    rrc_dest_name="rrc.hub",
    rrc_auto_reconnect=True,
    rrc_persist_sessions=True,
)
```

### Key Methods

- `get_landlock_status()`: Return Landlock LSM sandbox availability and
  activation state for the bot process
- `run(delay=10)`: Start the bot's main loop
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)`:
  Send a message to a destination, optionally with custom LXMF fields,
  stamp cost override, and opportunistic sending (tries direct, falls
  back to propagation immediately if configured).
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)`:
  Send a message with an attachment
- `command(name, description="No description provided", admin_only=False, threaded=False)`:
  Decorator for registering commands. Set `threaded=True` to run the
  command's callback in a separate thread. Commands support type-hinted
  arguments for automatic conversion.
- `intent(name, examples)`: Decorator for registering NLP intent
  handlers.
- `nlp.export_model()`: Export trained NLP model data.
- `nlp.import_model(model_data)`: Import previously exported NLP model
  data.
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)`:
  Request an RNS link to a destination. Allows custom `app_name` and
  `aspects` (defaults to "lxmf" and "delivery").
- `on_link(callback)`: Register a handler for incoming RNS links.
- `load_extension(name)`: Load a cog extension module by name (e.g.,
  "cogs.utility").
- `reload_extension(name)`: Reload a cog extension module.
- `add_cog(cog_instance)`: Add a cog class instance to the bot.
- `remove_cog(cog_name)`: Remove a cog from the bot by its class name.
- `on_first_message()`: Decorator for handling first messages from users
- `on_message()`: Decorator for handling all messages (called before
  command processing)
- `on_reaction()`: Decorator for handling inbound reactions. Handlers
  receive `(sender, reaction)` where reaction carries `reaction_to`,
  `reaction_emoji`, and `reaction_sender` keys
- `react(destination, message_hash, reaction)`: Send a reaction to a
  message via the LXMF `FIELD_REACTION` field
- `validate()`: Run validation checks on the bot configuration
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)`:
  Connect to an RRC hub as a client
- `disconnect_rrc(hub_hash=None)`: Disconnect one or all RRC hub
  sessions
- `on_rrc(callback=None)`: Decorator or register handler for RRC events
  (`handler(event, client, payload)`)
- `rrc`: `RRCManager` instance for multi-hub sessions

## Structured Commands via LXMF Fields

Bots can receive commands sent via LXMF `FIELD_COMMANDS` (`0x09`) and
automatically reply with `FIELD_RESULTS` (`0x0A`). This enables
structured request/response workflows alongside normal text commands.

Incoming `FIELD_COMMANDS` are parsed and routed through the same command
registry as text commands, sharing permission checks, type-hinted
argument parsing, threading, and middleware.

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields contains the raw LXMF fields dict
    # ctx.request_id is set automatically if the command included one
    ctx.reply("Bot is online")

# Sending a structured command from another LXMF client:
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# The bot reply automatically includes FIELD_RESULTS with the response and request_id.
```

To disable field command processing, set `lxmf_commands_enabled=False`
in `BotConfig`.

## Reactions

Reactions travel as the LXMF `FIELD_REACTION` (`0x40`) field on an
otherwise empty message. `pack_reaction` and `unpack_reaction` build
and parse that field.

``` python
from lxmfy import pack_reaction, unpack_reaction

# Send a reaction to a message
bot.react(destination_hash, message_hash_hex, "thumbs up emoji")

# Receive reactions
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  - hex hash of the target message
    # reaction["reaction_emoji"] - reaction text (up to 16 chars)
    # reaction["reaction_sender"] - sender
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

Reaction text is capped at 16 printable characters. The raw field stays
available in `ctx.fields` and `msg.fields` for compatibility.

## Storage

The framework provides three storage backends:

### JSONStorage

``` python
from lxmfy import JSONStorage

storage = JSONStorage("data")
```

### SQLiteStorage

``` python
from lxmfy import SQLiteStorage

storage = SQLiteStorage("data/bot.db")
```

### MemoryStorage

``` python
from lxmfy.storage import MemoryStorage

storage = MemoryStorage() # Entirely in-memory
```

## Commands

Command registration and handling:

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Type-Hinted Arguments

Commands automatically parse and convert arguments based on type hints
in the callback function.

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## Help System

The framework includes an interactive help generator that provides
beautiful, categorized help menus based on Cog and Command metadata.

``` python
# The help command is automatically registered.
# Users can use '/help' or '/help <command>'
```

### Threaded Commands

For long-running or blocking operations that do not interact with the
Reticulum Network Stack directly, you can run commands in a separate
thread to keep the bot responsive.

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # This runs in a separate thread
    ctx.reply("Long task completed!")
```

!!! warning "Thread safety"

    Functions marked as `threaded=True` **must not** directly interact
    with the Reticulum Network Stack (RNS) or any components that rely
    on `lxmfy.transport.py`, as these are generally not thread-safe.
    Use `ctx.reply()` for sending messages back to the user from within
    a threaded command.

## Events

Event system for handling various bot events:

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Handle message event
    pass
```

## Testing

Project tests include reliability and stress scenarios in the repository
test suite. Use the repository's test runner to execute them.

### Advanced Reliability Suite

The framework includes an extensive suite of automated tests for harsh
environments:

- **Manifold Testing**: Validates the mathematical topology of NLP
  intent vector space.
- **Chaos Engineering**: Simulates bit-rot, SD card failure, and storage
  corruption.
- **Temporal Drift**: Verifies resilience against system clock jumps (±1
  year).
- **Leak Detection**: Long-term tracking of memory, file descriptors,
  and threads.

## Permissions

Permission system for controlling access to bot features:

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## Middleware

Middleware system for processing messages and events:

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Process before command execution
    pass
```

## Attachments

Support for sending files, images, and audio:

``` python
from lxmfy import Attachment, AttachmentType

attachment = Attachment(
    type=AttachmentType.IMAGE,
    name="image.jpg",
    data=image_data,
    format="jpg"
)
bot.send_with_attachment(destination, "Here's an image", attachment)
```

## Icon Appearance (LXMF Field)

You can set a custom icon for your bot that compliant LXMF clients can
display. This uses the `LXMF.FIELD_ICON_APPEARANCE`.

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Required for LXMF.FIELD_ICON_APPEARANCE

# Define the icon appearance
icon_data = IconAppearance(
    icon_name="smart_toy",  # Name from Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # White foreground (3 bytes)
    bg_color=b'\x4A\x90\xE2'   # Blue background (3 bytes)
)

# Pack it into the LXMF field format
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Send a message with this icon
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# You can also combine it with other fields, like attachments:
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## Scheduler

Task scheduling system:

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Run daily at midnight
    pass
```

## Signatures

LXMFy provides configuration options for LXMF's built-in cryptographic
message signing and verification:

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # Enable signature checks
    require_message_signatures=False      # Set to True to reject unsigned messages
)
```

!!! note "Signature handling"

    LXMF automatically handles all cryptographic signing and
    verification using RNS identities. LXMFy's `SignatureManager` is a
    configuration layer that:

    - Controls whether to enforce signature verification
    - Determines policy for unsigned messages (accept or reject)
    - Integrates with the permission system (e.g., bypass verification
      for trusted users)

The actual cryptographic operations are performed by LXMF/RNS, not by
LXMFy.

### Landlock LSM Sandbox

On Linux kernels with Landlock support (5.13+), LXMFy can restrict
filesystem access for the bot process and for external script cogs.

**Bot process sandbox**

When `landlock_enabled=True` (default) and not running in `test_mode`,
the bot calls `apply_landlock_sandbox()` during initialization. System
directories are read-only; bot storage, config, cogs, Reticulum config,
and temp paths remain writable.

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# status keys: landlock_kernel_supported, landlock_requested,
# landlock_auto_enabled, landlock_disabled_by_env, landlock_active
```

**Environment override**

- `LXMFY_LANDLOCK=0`: disable Landlock even on supported kernels
- `LXMFY_LANDLOCK=1`: attempt Landlock on Linux regardless of
  auto-detection
- unset: follow `landlock_enabled` and kernel auto-detection

**External cog sandbox**

Script cogs use `external_cogs_sandbox_type`. In `auto` mode, Landlock
is preferred when available because it requires no external tools. See
the [Creating Bots](creating-bots.md) guide for the full sandbox
option list.

### Identity Pinning

LXMFy supports optional identity pinning to prevent impersonation if an
identity is rotated or compromised. When enabled, the bot "pins" an LXMF
address to its first-seen public key.

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### SignatureManager Methods

The `SignatureManager` is available as `bot.signature_manager` when
`signature_verification_enabled=True`:

- `should_verify_message(sender)`: Determine if a message from the given
  sender should be verified
- `handle_unsigned_message(sender, message_hash)`: Handle messages that
  lack valid signatures based on policy

### How LXMF Signatures Work

LXMF automatically signs all outgoing messages using the sender's RNS
identity during the `pack()` operation. When messages are received, LXMF
validates signatures and provides:

- `message.signature_validated`: Boolean indicating if the signature is
  valid
- `message.unverified_reason`: Reason code if validation failed (e.g.,
  `SIGNATURE_INVALID`, `SOURCE_UNKNOWN`)

LXMFy uses these built-in LXMF properties to enforce your bot's
signature policy.

## Message Delivery

LXMFy provides advanced message delivery features including propagation
nodes and automatic retries:

### Propagation Nodes

Send messages through specific propagation nodes for improved
reliability on the Reticulum network:

``` python
# Configure the propagation node once at config/runtime level
bot.set_propagation_node("<propagation_node_hash>")

# Send using configured delivery behavior
bot.send(
    destination_hash,
    "Message content"
)

# The propagation node hash should be a valid LXMF propagation node
# on the Reticulum network
```

### Automatic Retries

Configure automatic retry attempts for failed direct deliveries:

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # Retry direct delivery up to 5 times
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# Default direct_delivery_retries is 3
# Retry logic automatically handles delivery callbacks
```

The retry system tracks delivery attempts per destination and
automatically retries failed deliveries. Successful deliveries reset the
retry counter for that destination.

### Message Persistence

Outgoing messages can be persisted to disk to ensure they are delivered
even after a bot restart. Persistence is enabled by default. The
in-memory outbound queue is bounded (`message_queue_size`, default 50)
and drops the oldest message when full. Invalid destination hashes are
not restored.

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

### Router Controls

Thin wrappers over the underlying `LXMRouter` for sender control,
tickets, outbound queue management, and propagation node sync. All take
destination hashes as hex strings and return `False` when the router is
not running (for example in `test_mode`).

**Sender control (inbound)**

- `ignore_destination(destination)` / `unignore_destination(destination)` / `is_ignored(destination)`:
  Drop inbound messages from a sender
- `allow_destination(destination)` / `disallow_destination(destination)`:
  Whitelist management when the router runs in allow-list mode
- `prioritise_destination(destination)` / `unprioritise_destination(destination)`:
  Prioritized sender list
- `set_inbound_stamp_cost(stamp_cost)`: Require a stamp cost on inbound
  messages (`None` clears)
- `enforce_stamps()` / `ignore_stamps()`: Inbound stamp enforcement
  toggles

**Tickets**

- `generate_ticket(destination, expiry=None)`: Issue an inbound stamp
  ticket for a sender
- `get_inbound_tickets(destination)`: Tickets held for a sender
- `get_outbound_ticket(destination)` / `get_outbound_ticket_expiry(destination)` /
  `get_outbound_stamp_cost(destination)`: Outbound ticket state learned
  from the network

**Outbound queue**

- `outbound_queue()`: Snapshot of pending outbound messages
- `get_outbound_progress(lxm_hash)`: Delivery progress for a message
  hash, or `None`
- `cancel_outbound(message_id)`: Remove a queued message before
  delivery
- `delivery_link_available(destination)`: Whether an active RNS link
  exists to the destination

**Propagation**

- `sync_propagation_node(max_messages=None)`: Pull messages from the
  configured propagation node
- `cancel_propagation_sync()`: Stop an in-progress sync
- `get_propagation_stats()`: Node transfer state and limits, or `None`
- `set_retain_on_node(retain)`: Keep delivered messages on the node
- `announce_propagation_node()`: Announce this node as a propagation
  node
- `allow_control_identity(destination)` / `disallow_control_identity(destination)`:
  Propagation control channel whitelist

**Ingest**

- `ingest_lxm_uri(uri)`: Import an `lxm://` URI message into the
  inbound queue

## Message Handlers

LXMFy provides decorators for handling different types of incoming
messages:

### First Message Handler

Handle the first message from each user:

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # Return True to stop further processing
```

### General Message Handler

Handle all incoming messages before command processing:

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # Custom logic here
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # Stop further processing

    return False  # Continue to command processing
```

Message handlers are called in this order: 1. First message handler (if
this is the first message from this sender) 2. General message handlers
(registered with `on_message()`) 3. Command processing (if message
starts with command prefix)

## Reticulum Relay Chat (RRC)

Bots can join [RRC](https://rrc.kc1awv.net/) hubs over RNS Links with
CBOR envelopes. Package: `lxmfy.rrc`.

### BotConfig options

- `rrc_enabled` (bool, default `False`): Connect configured hubs on
  startup
- `rrc_hubs` (list of hex hashes): Hub destination hashes
- `rrc_rooms` (list of str): Rooms to auto-join after WELCOME
- `rrc_nick` (str or None): Nickname on HELLO and room messages
- `rrc_dest_name` (str, default `"rrc.hub"`): Destination name used to
  build the hub destination
- `rrc_auto_reconnect` (bool, default `True`): Reconnect after link loss
- `rrc_persist_sessions` (bool, default `True`): Persist hubs and rooms
  across restarts
- `reticulum_config_dir` (str or None): Reticulum config directory. Also
  set via `LXMFY_RETICULUM_CONFIG_DIR`. Use the same config as MeshChatX
  (often `~/.reticulum`) so hub announces are visible.

### Example

``` python
from lxmfy import LXMFBot, RRCMessage

bot = LXMFBot(
    name="RoomBot",
    reticulum_config_dir="~/.reticulum",
    rrc_enabled=True,
    rrc_hubs=["664fc0e8d2e448658e37bb3f34e6c88f"],
    rrc_rooms=["general"],
    rrc_nick="RoomBot",
)

@bot.on_rrc
def on_rrc(event, client, payload):
    if event == "msg" and isinstance(payload, RRCMessage) and payload.mention:
        client.send_message(payload.room, f"Hi {payload.nick}")

# Runtime API
# bot.connect_rrc(hub_hash, rooms=["general"])
# bot.rrc.send_message("general", "hello")
# bot.rrc.send_notice("general", "notice")
# bot.rrc.send_action("general", "waves")
# bot.rrc.join("ops")
# bot.rrc.part("ops")
# bot.rrc.status()
# bot.disconnect_rrc()
```

### Exported types

- `RRCClient`: Single-hub session
- `RRCManager`: Multi-hub manager (`bot.rrc`)
- `RRCMessage`: Room event payload (`kind`, `room`, `text`, `nick`,
  `src`, `mention`, ...)
- `RRC_VERSION`: Wire protocol version constant

Common events passed to `@bot.on_rrc` handlers include `status`,
`welcome`, `joined`, `parted`, `msg`, `notice`, `action`, `motd`,
`error`, and `rtt`.

# Templates

The framework includes several ready-to-use bot templates:

## EchoBot

Simple echo bot that repeats messages:

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

Note-taking bot with JSON storage:

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

Reminder bot with SQLite storage:

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

RRC room bot that joins configured hubs and replies to `@mentions`.
Defaults to hub `664fc0e8d2e448658e37bb3f34e6c88f`, room `#general`, and
`~/.reticulum` when available.

``` python
from lxmfy.templates import RRCBot

bot = RRCBot(
    hubs=["664fc0e8d2e448658e37bb3f34e6c88f"],
    rooms=["general"],
    nick="RRCBot",
    reticulum_config_dir="~/.reticulum",
)
bot.run()
```

# CLI Tools

The framework provides command-line tools for bot management:

``` bash
# Create a new bot
lxmfy create mybot

# Create a bot from template
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# Run a template bot
lxmfy run echo
lxmfy run rrc

# Test signature verification with a message
lxmfy signatures test

# Enable signature verification
lxmfy signatures enable

# Disable signature verification
lxmfy signatures disable
```

# Error Handling

Catch shutdown and runtime failures around `bot.run()`:

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# Module Reference

Generated from source docstrings.

::: lxmfy.LXMFBot

::: lxmfy.BotConfig

::: lxmfy.Attachment

::: lxmfy.AttachmentType

::: lxmfy.DefaultPerms

::: lxmfy.PermissionManager

::: lxmfy.TaskScheduler

::: lxmfy.ScheduledTask

::: lxmfy.Storage

::: lxmfy.JSONStorage

::: lxmfy.SQLiteStorage
