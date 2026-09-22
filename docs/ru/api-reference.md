# Основные компоненты

## LXMFBot

Основной класс бота, отвечающий за маршрутизацию сообщений, обработку команд и жизненный цикл бота.

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
    storage_type="json", # "json", "sqlite" или "memory"
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
    reticulum_config_dir=None,  # или LXMFY_RETICULUM_CONFIG_DIR / "~/.reticulum"
    rrc_enabled=False,
    rrc_hubs=[],
    rrc_rooms=[],
    rrc_nick=None,
    rrc_dest_name="rrc.hub",
    rrc_auto_reconnect=True,
    rrc_persist_sessions=True,
)
```

### Ключевые методы

- `get_landlock_status()`: состояние доступности и активации песочницы Landlock LSM для процесса бота
- `run(delay=10)`: запуск основного цикла бота
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)`: отправить сообщение получателю, опционально с полями LXMF, переопределением стоимости штампа и opportunistic-отправкой (пробует прямую доставку, сразу откатывается на propagation, если настроено)
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)`: отправить сообщение с вложением
- `react(destination, message_hash, reaction)`: отправить реакцию на сообщение (поле LXMF `FIELD_REACTION`)
- `command(name, description="No description provided", admin_only=False, threaded=False)`: декоратор регистрации команд. `threaded=True` запускает обработчик команды в отдельном потоке. Команды поддерживают аннотации типов для автоматического преобразования аргументов
- `intent(name, examples)`: декоратор регистрации обработчиков NLP-намерений
- `nlp.export_model()`: экспорт обученной модели NLP
- `nlp.import_model(model_data)`: импорт ранее экспортированной модели
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)`: запрос RNS Link к получателю. Позволяет задать свой `app_name` и `aspects` (по умолчанию "lxmf" и "delivery")
- `on_link(callback)`: регистрация обработчика входящих RNS Link
- `load_extension(name)`: загрузить модуль расширения кога по имени (например, "cogs.utility")
- `reload_extension(name)`: перезагрузить модуль расширения кога
- `add_cog(cog_instance)`: добавить экземпляр класса кога в бота
- `remove_cog(cog_name)`: удалить ког из бота по имени класса
- `on_first_message()`: декоратор обработки первых сообщений от пользователей
- `on_message()`: декоратор обработки всех сообщений (вызывается до обработки команд)
- `on_reaction()`: декоратор обработки входящих реакций; обработчик получает `(sender, reaction)` с ключами `reaction_to`, `reaction_emoji`, `reaction_sender`
- `validate()`: проверка конфигурации бота
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)`: подключение к RRC-хабу как клиент
- `disconnect_rrc(hub_hash=None)`: отключение одной или всех сессий RRC-хабов
- `on_rrc(callback=None)`: декоратор или регистрация обработчика событий RRC (`handler(event, client, payload)`)
- `rrc`: экземпляр `RRCManager` для сессий с несколькими хабами

## Структурированные команды через поля LXMF

Боты могут принимать команды, отправленные через `FIELD_COMMANDS` (`0x09`) LXMF, и автоматически отвечать с `FIELD_RESULTS` (`0x0A`). Это даёт структурированные запросы и ответы наряду с обычными текстовыми командами.

Входящие `FIELD_COMMANDS` разбираются и направляются через тот же реестр команд, что и текстовые, с общими проверками прав, разбором аргументов по аннотациям, потоками и middleware.

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields содержит исходный словарь полей LXMF
    # ctx.request_id устанавливается автоматически, если команда его включала
    ctx.reply("Bot is online")

# Отправка структурированной команды из другого клиента LXMF:
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# Ответ бота автоматически включает FIELD_RESULTS с ответом и request_id.
```

Чтобы отключить обработку полевых команд, установите `lxmf_commands_enabled=False` в `BotConfig`.

## Реакции

Реакции передаются полем `FIELD_REACTION` (`0x40`) LXMF поверх пустого сообщения. `pack_reaction` и `unpack_reaction` собирают и разбирают это поле.

``` python
from lxmfy import pack_reaction, unpack_reaction

# Отправка реакции на сообщение
bot.react(destination_hash, message_hash_hex, "\U0001F44D")

# Приём реакций
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  — hex-хэш целевого сообщения
    # reaction["reaction_emoji"] — текст реакции (до 16 символов)
    # reaction["reaction_sender"] — отправитель
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

Текст реакции обрезается до 16 печатаемых символов. Исходное поле остаётся доступным в `ctx.fields` и `msg.fields` для совместимости.

## Хранилище

Фреймворк предоставляет три бэкенда хранилища:

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

storage = MemoryStorage() # Полностью в памяти
```

## Команды

Регистрация и обработка команд:

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Аргументы с аннотациями типов

Команды автоматически разбирают и преобразуют аргументы на основе аннотаций типов в функции-обработчике.

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## Система помощи

Фреймворк включает интерактивный генератор помощи с категоризированными меню на основе метаданных когов и команд.

``` python
# Команда help регистрируется автоматически.
# Пользователи могут использовать '/help' или '/help <command>'
```

### Потоковые команды

Для долгих или блокирующих операций, которые не взаимодействуют напрямую с Reticulum Network Stack, команды можно запускать в отдельном потоке, чтобы бот оставался отзывчивым.

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # Выполняется в отдельном потоке
    ctx.reply("Long task completed!")
```

**Важно:** функции с `threaded=True` **не должны** напрямую взаимодействовать с Reticulum Network Stack (RNS) или компонентами, зависящими от `lxmfy.transport.py`, так как они в общем случае не потокобезопасны. Используйте `ctx.reply()` для отправки сообщений пользователю из потоковой команды.

## События

Система событий для обработки различных событий бота:

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Обработка события сообщения
    pass
```

## Тестирование

Тесты проекта включают сценарии надёжности и нагрузки в тестовом наборе репозитория. Используйте тест-раннер репозитория для их запуска.

### Расширенный набор проверок надёжности

Фреймворк включает обширный набор автоматизированных тестов для суровых условий:

- **Manifold Testing**: проверка математической топологии векторного пространства намерений NLP.
- **Chaos Engineering**: симуляция битовой гнили, отказа SD-карты и порчи хранилища.
- **Temporal Drift**: проверка устойчивости к скачкам системных часов (±1 год).
- **Leak Detection**: долгосрочное отслеживание памяти, файловых дескрипторов и потоков.

## Права доступа

Система прав для контроля доступа к возможностям бота:

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## Middleware

Система middleware для обработки сообщений и событий:

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Обработка до выполнения команды
    pass
```

## Вложения

Поддержка отправки файлов, изображений и аудио:

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

## Внешний вид иконки (поле LXMF)

Боту можно назначить пользовательскую иконку, которую отображают совместимые клиенты LXMF. Используется `LXMF.FIELD_ICON_APPEARANCE`.

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Требуется для LXMF.FIELD_ICON_APPEARANCE

# Определяем внешний вид иконки
icon_data = IconAppearance(
    icon_name="smart_toy",  # Имя из Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # Белый передний план (3 байта)
    bg_color=b'\x4A\x90\xE2'   # Синий фон (3 байта)
)

# Упаковываем в формат поля LXMF
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Отправляем сообщение с этой иконкой
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# Можно комбинировать с другими полями, например с вложениями:
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## Планировщик

Система планирования задач:

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Выполняется ежедневно в полночь
    pass
```

## Подписи

LXMFy предоставляет настройки для встроенной криптографической подписи и проверки сообщений LXMF:

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # Включить проверку подписей
    require_message_signatures=False      # True — отклонять неподписанные сообщения
)
```

**Важно:** LXMF автоматически выполняет все криптографические операции подписи и проверки с идентификаторами RNS. `SignatureManager` в LXMFy — это слой конфигурации, который:

- Управляет тем, применять ли проверку подписей
- Определяет политику для неподписанных сообщений (принимать или отклонять)
- Интегрируется с системой прав (например, обход проверки для доверенных пользователей)

Сами криптографические операции выполняет LXMF/RNS, а не LXMFy.

### Песочница Landlock LSM

На ядрах Linux с поддержкой Landlock (5.13+) LXMFy может ограничивать доступ к файловой системе для процесса бота и для внешних скриптовых когов.

**Песочница процесса бота**

Когда `landlock_enabled=True` (по умолчанию) и бот не запущен в `test_mode`, бот вызывает `apply_landlock_sandbox()` при инициализации. Системные каталоги доступны только для чтения; хранилище бота, конфигурация, коги, конфигурация Reticulum и временные пути остаются записываемыми.

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# ключи status: landlock_kernel_supported, landlock_requested,
# landlock_auto_enabled, landlock_disabled_by_env, landlock_active
```

**Переопределение через окружение**

- `LXMFY_LANDLOCK=0`: отключить Landlock даже на поддерживаемых ядрах
- `LXMFY_LANDLOCK=1`: попытаться применить Landlock в Linux независимо от автоопределения
- не задано: следовать `landlock_enabled` и автоопределению ядра

**Песочница внешних когов**

Скриптовые коги используют `external_cogs_sandbox_type`. В режиме `auto` предпочитается Landlock, так как ему не нужны внешние инструменты. Полный список вариантов песочницы — в руководстве [Создание ботов](creating-bots.md).

### Закрепление идентификатора

LXMFy поддерживает опциональное закрепление идентификатора (pinning) для защиты от подмены при ротации или компрометации идентификатора. Когда включено, бот «закрепляет» LXMF-адрес за первым увиденным открытым ключом.

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### Методы SignatureManager

`SignatureManager` доступен как `bot.signature_manager`, когда `signature_verification_enabled=True`:

- `should_verify_message(sender)`: определить, нужно ли проверять сообщение от данного отправителя
- `handle_unsigned_message(sender, message_hash)`: обработать сообщения без валидной подписи согласно политике

### Как работают подписи LXMF

LXMF автоматически подписывает все исходящие сообщения идентификатором RNS отправителя во время операции `pack()`. При получении сообщений LXMF проверяет подписи и предоставляет:

- `message.signature_validated`: булево значение валидности подписи
- `message.unverified_reason`: код причины при неудачной проверке (например, `SIGNATURE_INVALID`, `SOURCE_UNKNOWN`)

LXMFy использует эти встроенные свойства LXMF для применения политики подписей бота.

## Доставка сообщений

LXMFy предоставляет расширенные возможности доставки, включая узлы распространения и автоматические повторы:

### Узлы распространения

Отправка сообщений через конкретные узлы распространения для повышения надёжности в сети Reticulum:

``` python
# Настройте узел распространения один раз на уровне конфигурации/времени выполнения
bot.set_propagation_node("<propagation_node_hash>")

# Отправка с настроенным поведением доставки
bot.send(
    destination_hash,
    "Message content"
)

# Хэш узла распространения должен быть валидным узлом распространения LXMF
# в сети Reticulum
```

### Автоматические повторы

Настройка автоматических повторных попыток для неудачных прямых доставок:

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # Повторять прямую доставку до 5 раз
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# direct_delivery_retries по умолчанию равно 3
# Логика повторов автоматически обрабатывает обратные вызовы доставки
```

Система повторов отслеживает попытки доставки по каждому получателю и автоматически повторяет неудачные доставки. Успешные доставки сбрасывают счётчик повторов для этого получателя.

### Персистентность сообщений

Исходящие сообщения можно сохранять на диск, чтобы они доставлялись даже после перезапуска бота. Персистентность включена по умолчанию. Очередь исходящих в памяти ограничена (`message_queue_size`, по умолчанию 50) и при переполнении отбрасывает самое старое сообщение. Невалидные хэши получателей не восстанавливаются.

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

## Обработчики сообщений

LXMFy предоставляет декораторы для обработки разных типов входящих сообщений:

### Обработчик первого сообщения

Обработка первого сообщения от каждого пользователя:

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # Верните True, чтобы остановить дальнейшую обработку
```

### Общий обработчик сообщений

Обработка всех входящих сообщений до обработки команд:

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # Своя логика здесь
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # Остановить дальнейшую обработку

    return False  # Перейти к обработке команд
```

Обработчики сообщений вызываются в таком порядке: 1. обработчик первого сообщения (если это первое сообщение от отправителя) 2. общие обработчики (зарегистрированные через `on_message()`) 3. обработка команд (если сообщение начинается с префикса команды)

## Reticulum Relay Chat (RRC)

Боты могут подключаться к хабам [RRC](https://rrc.kc1awv.net/) по RNS Link с конвертами CBOR. Пакет: `lxmfy.rrc`.

### Опции BotConfig

- `rrc_enabled` (bool, по умолчанию `False`): подключать настроенные хабы при запуске
- `rrc_hubs` (список hex-хэшей): хэши получателей хабов
- `rrc_rooms` (список строк): комнаты для авто-join после WELCOME
- `rrc_nick` (строка или None): никнейм в HELLO и сообщениях комнат
- `rrc_dest_name` (строка, по умолчанию `"rrc.hub"`): имя получателя для построения destination хаба
- `rrc_auto_reconnect` (bool, по умолчанию `True`): переподключение после потери link
- `rrc_persist_sessions` (bool, по умолчанию `True`): сохранять хабы и комнаты между перезапусками
- `reticulum_config_dir` (строка или None): каталог конфигурации Reticulum. Также задаётся через `LXMFY_RETICULUM_CONFIG_DIR`. Используйте ту же конфигурацию, что у MeshChatX (часто `~/.reticulum`), чтобы анонсы хаба были видны.

### Пример

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

# API времени выполнения
# bot.connect_rrc(hub_hash, rooms=["general"])
# bot.rrc.send_message("general", "hello")
# bot.rrc.send_notice("general", "notice")
# bot.rrc.send_action("general", "waves")
# bot.rrc.join("ops")
# bot.rrc.part("ops")
# bot.rrc.status()
# bot.disconnect_rrc()
```

### Экспортируемые типы

- `RRCClient`: сессия с одним хабом
- `RRCManager`: менеджер нескольких хабов (`bot.rrc`)
- `RRCMessage`: данные события комнаты (`kind`, `room`, `text`, `nick`, `src`, `mention`, ...)
- `RRC_VERSION`: константа версии проводного протокола

Типичные события, передаваемые обработчикам `@bot.on_rrc`: `status`, `welcome`, `joined`, `parted`, `msg`, `notice`, `action`, `motd`, `error` и `rtt`.

# Шаблоны

Фреймворк включает несколько готовых шаблонов ботов:

## EchoBot

Простой echo-бот, повторяющий сообщения:

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

Бот для заметок с хранилищем JSON:

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

Бот-напоминалка с хранилищем SQLite:

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

RRC-бот для комнат: подключается к настроенным хабам и отвечает на `@упоминания`. По умолчанию хаб `664fc0e8d2e448658e37bb3f34e6c88f`, комната `#general` и `~/.reticulum`, если доступен.

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

# Инструменты CLI

Фреймворк предоставляет инструменты командной строки для управления ботами:

``` bash
# Создать нового бота
lxmfy create mybot

# Создать бота из шаблона
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# Запустить шаблонного бота
lxmfy run echo
lxmfy run rrc

# Проверить проверку подписей сообщением
lxmfy signatures test

# Включить проверку подписей
lxmfy signatures enable

# Отключить проверку подписей
lxmfy signatures disable
```

# Обработка ошибок

Перехватывайте завершение работы и ошибки выполнения вокруг `bot.run()`:

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# Справочник модулей

Генерируется из строк документации исходного кода.

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
