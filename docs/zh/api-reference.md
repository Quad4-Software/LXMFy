# 核心组件

## LXMFBot

主机器人类，负责消息路由、命令处理和机器人生命周期管理。

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
    storage_type="json", # "json"、"sqlite" 或 "memory"
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
    external_cogs_sandbox_type="auto",  # "auto"、"landlock"、"bwrap"、"firejail"、"none"
    external_cogs_timeout=30,
    landlock_enabled=True,
    nlp_enabled=False,
    nlp_threshold=0.5,
    link_support_enabled=False,
    lxmf_commands_enabled=True,
    message_queue_size=50,
    reticulum_config_dir=None,  # 或 LXMFY_RETICULUM_CONFIG_DIR / "~/.reticulum"
    rrc_enabled=False,
    rrc_hubs=[],
    rrc_rooms=[],
    rrc_nick=None,
    rrc_dest_name="rrc.hub",
    rrc_auto_reconnect=True,
    rrc_persist_sessions=True,
)
```

### 主要方法

- `get_landlock_status()`：返回机器人进程的 Landlock LSM 沙箱
  可用性和激活状态
- `run(delay=10)`：启动机器人主循环
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)`：
  向目标发送消息，可选携带自定义 LXMF 字段、邮票成本覆盖和
  机会式发送（先尝试直接投递，若已配置则立即回退到传播
  节点）。
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)`：
  发送带附件的消息
- `command(name, description="No description provided", admin_only=False, threaded=False)`：
  注册命令的装饰器。设 `threaded=True` 可在独立线程中运行
  命令回调。命令支持带类型注解的参数，可自动转换。
- `intent(name, examples)`：注册 NLP 意图处理器的装饰器。
- `nlp.export_model()`：导出训练好的 NLP 模型数据。
- `nlp.import_model(model_data)`：导入之前导出的 NLP 模型
  数据。
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)`：
  向目标请求一条 RNS link。允许自定义 `app_name` 和
  `aspects`（默认为 "lxmf" 和 "delivery"）。
- `on_link(callback)`：注册传入 RNS link 的处理器。
- `load_extension(name)`：按名称加载 Cog 扩展模块（例如
  "cogs.utility"）。
- `reload_extension(name)`：重载 Cog 扩展模块。
- `add_cog(cog_instance)`：向机器人添加一个 Cog 类实例。
- `remove_cog(cog_name)`：按类名从机器人移除一个 Cog。
- `on_first_message()`：处理用户首条消息的装饰器
- `on_message()`：处理所有消息的装饰器（在命令处理之前
  调用）
- `on_reaction()`：处理传入回应的装饰器。处理器接收
  `(sender, reaction)`，其中 reaction 带有 `reaction_to`、
  `reaction_emoji` 和 `reaction_sender` 键
- `react(destination, message_hash, reaction)`：通过 LXMF
  `FIELD_REACTION` 字段对一条消息发送回应
- `validate()`：对机器人配置运行校验检查
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)`：
  作为客户端连接到 RRC hub
- `disconnect_rrc(hub_hash=None)`：断开一个或全部 RRC hub
  会话
- `on_rrc(callback=None)`：注册 RRC 事件处理器的装饰器或方法
  （`handler(event, client, payload)`）
- `rrc`：用于多 hub 会话的 `RRCManager` 实例

## 通过 LXMF 字段实现结构化命令

机器人可以接收通过 LXMF `FIELD_COMMANDS`（`0x09`）发送的命令，
并自动以 `FIELD_RESULTS`（`0x0A`）回复。这让结构化请求/响应
工作流可以与普通文本命令并存。

传入的 `FIELD_COMMANDS` 会被解析并路由到与文本命令相同的命令
注册表，共享权限检查、类型注解参数解析、线程化和中间件。

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields 包含原始 LXMF 字段字典
    # 如果命令带有 request_id，ctx.request_id 会自动设置
    ctx.reply("Bot is online")

# 从另一个 LXMF 客户端发送结构化命令：
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# 机器人的回复会自动包含 FIELD_RESULTS，其中有响应内容和 request_id。
```

要禁用字段命令处理，在 `BotConfig` 中设置
`lxmf_commands_enabled=False`。

## 回应

回应以 LXMF `FIELD_REACTION`（`0x40`）字段的形式承载在一条
其余部分为空的消息上。`pack_reaction` 和 `unpack_reaction`
用于构造和解析该字段。

``` python
from lxmfy import pack_reaction, unpack_reaction

# 对一条消息发送回应
bot.react(destination_hash, message_hash_hex, "thumbs up emoji")

# 接收回应
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  - 目标消息的十六进制哈希
    # reaction["reaction_emoji"] - 回应文本（最多 16 个字符）
    # reaction["reaction_sender"] - 发送者
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

回应文本上限为 16 个可打印字符。原始字段仍可在 `ctx.fields`
和 `msg.fields` 中访问以保持兼容。

## 存储

框架提供三种存储后端：

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

storage = MemoryStorage() # 完全在内存中
```

## 命令

命令注册和处理：

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### 类型注解参数

命令会根据回调函数中的类型注解自动解析和转换参数。

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## 帮助系统

框架内置交互式帮助生成器，基于 Cog 和 Command 元数据生成
美观、分类的帮助菜单。

``` python
# help 命令会自动注册。
# 用户可以使用 '/help' 或 '/help <command>'
```

### 线程化命令

对于不直接与 Reticulum Network Stack 交互的耗时或阻塞操作，
可以让命令在独立线程中运行，保持机器人响应性。

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # 这在独立线程中运行
    ctx.reply("Long task completed!")
```

!!! warning "线程安全"

    标记为 `threaded=True` 的函数**不得**直接与 Reticulum
    Network Stack（RNS）或任何依赖 `lxmfy.transport.py` 的组件
    交互，因为它们通常不是线程安全的。在线程化命令中向用户
    回发消息请使用 `ctx.reply()`。

## 事件

用于处理各种机器人事件的事件系统：

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # 处理消息事件
    pass
```

## 测试

项目测试包含仓库测试套件中的可靠性和压力场景。使用仓库的
测试运行器执行它们。

### 高级可靠性测试套件

框架包含一套针对严苛环境的大规模自动化测试：

- **Manifold Testing**：校验 NLP 意图向量空间的数学拓扑。
- **Chaos Engineering**：模拟位衰减、SD 卡故障和存储损坏。
- **Temporal Drift**：验证对系统时钟跳变（±1 年）的抵抗力。
- **Leak Detection**：长期跟踪内存、文件描述符和线程。

## 权限

用于控制机器人功能访问的权限系统：

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## 中间件

用于处理消息和事件的中间件系统：

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # 在命令执行前处理
    pass
```

## 附件

支持发送文件、图片和音频：

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

## 图标外观（LXMF 字段）

你可以为机器人设置自定义图标，兼容的 LXMF 客户端可以显示它。
这使用 `LXMF.FIELD_ICON_APPEARANCE`。

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # 需要 LXMF.FIELD_ICON_APPEARANCE

# 定义图标外观
icon_data = IconAppearance(
    icon_name="smart_toy",  # 来自 Material Symbols 的名称
    fg_color=b'\xFF\xFF\xFF',  # 白色前景（3 字节）
    bg_color=b'\x4A\x90\xE2'   # 蓝色背景（3 字节）
)

# 打包成 LXMF 字段格式
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# 发送带此图标的消息
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# 也可以与其他字段组合，例如附件：
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## 调度器

任务调度系统：

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # 每天午夜运行
    pass
```

## 签名

LXMFy 为 LXMF 内置的加密消息签名与校验提供配置选项：

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # 启用签名检查
    require_message_signatures=False      # 设为 True 可拒绝未签名消息
)
```

!!! note "签名处理"

    LXMF 使用 RNS 身份自动处理所有加密签名和校验。LXMFy 的
    `SignatureManager` 是一个配置层，负责：

    - 控制是否强制执行签名校验
    - 确定对未签名消息的策略（接受或拒绝）
    - 与权限系统集成（例如可信用户可跳过校验）

实际的加密操作由 LXMF/RNS 执行，而不是 LXMFy。

### Landlock LSM 沙箱

在支持 Landlock 的 Linux 内核（5.13+）上，LXMFy 可以限制
机器人进程和外部脚本 Cog 的文件系统访问。

**机器人进程沙箱**

当 `landlock_enabled=True`（默认）且未运行于 `test_mode` 时，
机器人会在初始化期间调用 `apply_landlock_sandbox()`。系统目录
为只读；机器人存储、配置、Cog、Reticulum 配置和临时路径保持
可写。

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# status 的键：landlock_kernel_supported、landlock_requested、
# landlock_auto_enabled、landlock_disabled_by_env、landlock_active
```

**环境变量覆盖**

- `LXMFY_LANDLOCK=0`：即使内核支持也禁用 Landlock
- `LXMFY_LANDLOCK=1`：在 Linux 上无论自动检测结果如何都尝试
  Landlock
- 未设置：遵循 `landlock_enabled` 和内核自动检测

**外部 Cog 沙箱**

脚本 Cog 使用 `external_cogs_sandbox_type`。在 `auto` 模式下
优先使用 Landlock（若可用），因为它不需要外部工具。完整的
沙箱选项列表见[创建机器人](creating-bots.md)指南。

### 身份固定

LXMFy 支持可选的身份固定，防止身份被轮换或泄露后遭到冒充。
启用后，机器人会把一个 LXMF 地址“固定”到首次见到的公钥。

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### SignatureManager 方法

当 `signature_verification_enabled=True` 时，可通过
`bot.signature_manager` 访问 `SignatureManager`：

- `should_verify_message(sender)`：判断来自给定发送者的消息
  是否应校验
- `handle_unsigned_message(sender, message_hash)`：按策略处理
  缺少有效签名的消息

### LXMF 签名的工作原理

LXMF 在 `pack()` 操作期间使用发送者的 RNS 身份自动为所有出站
消息签名。接收消息时，LXMF 校验签名并提供：

- `message.signature_validated`：布尔值，表示签名是否有效
- `message.unverified_reason`：校验失败时的原因码（例如
  `SIGNATURE_INVALID`、`SOURCE_UNKNOWN`）

LXMFy 使用这些 LXMF 内置属性来执行机器人的签名策略。

## 消息投递

LXMFy 提供高级消息投递功能，包括传播节点和自动重试：

### 传播节点

通过特定传播节点发送消息，提高在 Reticulum 网络上的可靠性：

``` python
# 在配置/运行时层面只设置一次传播节点
bot.set_propagation_node("<propagation_node_hash>")

# 按配置好的投递行为发送
bot.send(
    destination_hash,
    "Message content"
)

# 传播节点哈希应该是 Reticulum 网络上
# 一个有效的 LXMF 传播节点
```

### 自动重试

为失败的直接投递配置自动重试次数：

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # 直接投递最多重试 5 次
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# direct_delivery_retries 默认为 3
# 重试逻辑会自动处理投递回调
```

重试系统会跟踪每个目标的投递尝试次数，并自动重试失败的投递。
投递成功后会重置该目标的重试计数器。

### 消息持久化

出站消息可以持久化到磁盘，确保机器人重启后仍能送达。持久化
默认开启。内存出站队列有上限（`message_queue_size`，默认 50），
满了之后会丢弃最旧的消息。无效的目标哈希不会被恢复。

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

## 消息处理器

LXMFy 提供用于处理不同类型传入消息的装饰器：

### 首条消息处理器

处理每个用户的首条消息：

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # 返回 True 停止进一步处理
```

### 通用消息处理器

在命令处理之前处理所有传入消息：

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # 此处为自定义逻辑
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # 停止进一步处理

    return False  # 继续到命令处理
```

消息处理器按以下顺序调用：1. 首条消息处理器（如果这是该
发送者的首条消息）2. 通用消息处理器（通过 `on_message()`
注册）3. 命令处理（如果消息以命令前缀开头）

## Reticulum Relay Chat (RRC)

机器人可以通过 RNS Link 以 CBOR 封包加入
[RRC](https://rrc.kc1awv.net/) hub。包：`lxmfy.rrc`。

### BotConfig 选项

- `rrc_enabled`（bool，默认 `False`）：启动时连接已配置的
  hub
- `rrc_hubs`（十六进制哈希列表）：hub 目标哈希
- `rrc_rooms`（str 列表）：WELCOME 之后自动加入的房间
- `rrc_nick`（str 或 None）：HELLO 和房间消息中的昵称
- `rrc_dest_name`（str，默认 `"rrc.hub"`）：用于构造 hub
  目标的目标名称
- `rrc_auto_reconnect`（bool，默认 `True`）：link 断开后自动
  重连
- `rrc_persist_sessions`（bool，默认 `True`）：跨重启持久化
  hub 和房间
- `reticulum_config_dir`（str 或 None）：Reticulum 配置目录。
  也可用 `LXMFY_RETICULUM_CONFIG_DIR` 设置。使用与 MeshChatX
  相同的配置（通常是 `~/.reticulum`），这样 hub 的 announce
  才可见。

### 示例

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

# 运行时 API
# bot.connect_rrc(hub_hash, rooms=["general"])
# bot.rrc.send_message("general", "hello")
# bot.rrc.send_notice("general", "notice")
# bot.rrc.send_action("general", "waves")
# bot.rrc.join("ops")
# bot.rrc.part("ops")
# bot.rrc.status()
# bot.disconnect_rrc()
```

### 导出类型

- `RRCClient`：单 hub 会话
- `RRCManager`：多 hub 管理器（`bot.rrc`）
- `RRCMessage`：房间事件负载（`kind`、`room`、`text`、
  `nick`、`src`、`mention` 等）
- `RRC_VERSION`：线路协议版本常量

传给 `@bot.on_rrc` 处理器的常见事件包括 `status`、`welcome`、
`joined`、`parted`、`msg`、`notice`、`action`、`motd`、
`error` 和 `rtt`。

# 模板

框架包含若干可直接使用的机器人模板：

## EchoBot

简单的 echo 机器人，复述收到的消息：

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

使用 JSON 存储的笔记机器人：

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

使用 SQLite 存储的提醒机器人：

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

RRC 房间机器人，加入配置的 hub 并回复 `@提及`。默认 hub 为
`664fc0e8d2e448658e37bb3f34e6c88f`，房间为 `#general`，并在
可用时使用 `~/.reticulum`。

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

# CLI 工具

框架提供用于机器人管理的命令行工具：

``` bash
# 创建一个新机器人
lxmfy create mybot

# 从模板创建机器人
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# 运行模板机器人
lxmfy run echo
lxmfy run rrc

# 用一条消息测试签名校验
lxmfy signatures test

# 启用签名校验
lxmfy signatures enable

# 禁用签名校验
lxmfy signatures disable
```

# 错误处理

在 `bot.run()` 周围捕获关停和运行时故障：

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# 模块参考

由源码 docstring 生成。

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
