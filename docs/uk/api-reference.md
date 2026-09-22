# Основні компоненти

## LXMFBot

Головний клас бота, який обробляє маршрутизацію повідомлень, обробку
команд і керування життєвим циклом бота.

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
    storage_type="json", # "json", "sqlite" або "memory"
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
    reticulum_config_dir=None,  # або LXMFY_RETICULUM_CONFIG_DIR / "~/.reticulum"
    rrc_enabled=False,
    rrc_hubs=[],
    rrc_rooms=[],
    rrc_nick=None,
    rrc_dest_name="rrc.hub",
    rrc_auto_reconnect=True,
    rrc_persist_sessions=True,
)
```

### Ключові методи

- `get_landlock_status()`: повертає доступність і стан активації
  пісочниці Landlock LSM для процесу бота
- `run(delay=10)`: запускає головний цикл бота
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)`:
  надсилає повідомлення отримувачу, опційно з власними полями LXMF,
  перевизначенням вартості штампа та опортуністичним надсиланням
  (намагається доставити напряму, одразу переходить на propagation,
  якщо налаштовано).
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)`:
  надсилає повідомлення з вкладенням
- `command(name, description="No description provided", admin_only=False, threaded=False)`:
  декоратор для реєстрації команд. Встановіть `threaded=True`, щоб
  виконувати зворотний виклик команди в окремому потоці. Команди
  підтримують типізовані аргументи для автоматичного перетворення.
- `intent(name, examples)`: декоратор для реєстрації обробників
  NLP-інтентів.
- `nlp.export_model()`: експортує дані навченої NLP-моделі.
- `nlp.import_model(model_data)`: імпортує раніше експортовані дані
  NLP-моделі.
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)`:
  запитує RNS link до отримувача. Дозволяє власні `app_name` і
  `aspects` (типово "lxmf" і "delivery").
- `on_link(callback)`: реєструє обробник вхідних RNS link.
- `load_extension(name)`: завантажує модуль розширення-коґа за ім'ям
  (наприклад, "cogs.utility").
- `reload_extension(name)`: перезавантажує модуль розширення-коґа.
- `add_cog(cog_instance)`: додає екземпляр класу коґа до бота.
- `remove_cog(cog_name)`: видаляє коґ з бота за ім'ям його класу.
- `on_first_message()`: декоратор для обробки перших повідомлень від
  користувачів
- `on_message()`: декоратор для обробки всіх повідомлень (викликається
  до обробки команд)
- `on_reaction()`: декоратор для обробки вхідних реакцій. Обробники
  отримують `(sender, reaction)`, де reaction містить ключі
  `reaction_to`, `reaction_emoji` і `reaction_sender`
- `react(destination, message_hash, reaction)`: надсилає реакцію на
  повідомлення через поле LXMF `FIELD_REACTION`
- `validate()`: запускає перевірки конфігурації бота
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)`:
  підключається до хаба RRC як клієнт
- `disconnect_rrc(hub_hash=None)`: відключає одну або всі сесії хабів
  RRC
- `on_rrc(callback=None)`: декоратор або реєстрація обробника подій RRC
  (`handler(event, client, payload)`)
- `rrc`: екземпляр `RRCManager` для сесій з кількома хабами

## Структуровані команди через поля LXMF

Боти можуть отримувати команди, надіслані через `FIELD_COMMANDS`
(`0x09`) LXMF, і автоматично відповідати з `FIELD_RESULTS` (`0x0A`). Це
вмикає структуровані процеси запит/відповідь поруч із звичайними
текстовими командами.

Вхідні `FIELD_COMMANDS` розбираються і спрямовуються через той самий
реєстр команд, що й текстові команди, зі спільними перевірками прав,
розбором типізованих аргументів, потоками та middleware.

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields містить сирий словник полів LXMF
    # ctx.request_id встановлюється автоматично, якщо команда його містила
    ctx.reply("Bot is online")

# Надсилання структурованої команди з іншого клієнта LXMF:
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# Відповідь бота автоматично містить FIELD_RESULTS з відповіддю та request_id.
```

Щоб вимкнути обробку польових команд, задайте
`lxmf_commands_enabled=False` у `BotConfig`.

## Реакції

Реакції передаються як поле LXMF `FIELD_REACTION` (`0x40`) на інакше
порожньому повідомленні. `pack_reaction` і `unpack_reaction` будують і
розбирають це поле.

``` python
from lxmfy import pack_reaction, unpack_reaction

# Надіслати реакцію на повідомлення
bot.react(destination_hash, message_hash_hex, "thumbs up emoji")

# Отримувати реакції
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  - hex-хеш цільового повідомлення
    # reaction["reaction_emoji"] - текст реакції (до 16 символів)
    # reaction["reaction_sender"] - відправник
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

Текст реакції обмежений 16 друкованими символами. Сире поле лишається
доступним у `ctx.fields` і `msg.fields` для сумісності.

## Сховище

Фреймворк надає три бекенди сховища:

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

storage = MemoryStorage() # Повністю в пам'яті
```

## Команди

Реєстрація та обробка команд:

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Типізовані аргументи

Команди автоматично розбирають і перетворюють аргументи на основі
анотацій типів у функції зворотного виклику.

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## Система довідки

Фреймворк включає інтерактивний генератор довідки, який створює
категоризовані меню довідки на основі метаданих коґів і команд.

``` python
# Команда help реєструється автоматично.
# Користувачі можуть використовувати '/help' або '/help <command>'
```

### Команди в окремому потоці

Для довготривалих або блокуючих операцій, які не взаємодіють із
Reticulum Network Stack напряму, ви можете виконувати команди в окремому
потоці, щоб бот лишався чутливим.

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # Це виконується в окремому потоці
    ctx.reply("Long task completed!")
```

!!! warning "Безпека потоків"

    Функції, позначені `threaded=True`, **не повинні** напряму
    взаємодіяти з Reticulum Network Stack (RNS) або будь-якими
    компонентами, які покладаються на `lxmfy.transport.py`, оскільки
    вони загалом не є потокобезпечними. Використовуйте `ctx.reply()` для
    надсилання повідомлень користувачу зсередини команди в окремому
    потоці.

## Події

Система подій для обробки різних подій бота:

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Обробка події повідомлення
    pass
```

## Тестування

Тести проєкту включають сценарії надійності та навантаження в тестовому
наборі репозиторію. Використовуйте тестовий раннер репозиторію для їх
виконання.

### Розширений набір перевірок надійності

Фреймворк включає великий набір автоматизованих тестів для суворих
умов:

- **Manifold Testing**: перевіряє математичну топологію векторного
  простору NLP-інтентів.
- **Chaos Engineering**: імітує bit-rot, відмову SD-карти та пошкодження
  сховища.
- **Temporal Drift**: перевіряє стійкість до стрибків системного
  годинника (±1 рік).
- **Leak Detection**: довготермінове відстеження пам'яті, файлових
  дескрипторів і потоків.

## Права доступу

Система прав для керування доступом до функцій бота:

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## Middleware

Система middleware для обробки повідомлень і подій:

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Обробка перед виконанням команди
    pass
```

## Вкладення

Підтримка надсилання файлів, зображень і аудіо:

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

## Вигляд іконки (поле LXMF)

Ви можете задати власну іконку для бота, яку сумісні клієнти LXMF можуть
відображати. Для цього використовується `LXMF.FIELD_ICON_APPEARANCE`.

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Потрібен для LXMF.FIELD_ICON_APPEARANCE

# Визначаємо вигляд іконки
icon_data = IconAppearance(
    icon_name="smart_toy",  # Ім'я з Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # Білий передній план (3 байти)
    bg_color=b'\x4A\x90\xE2'   # Синій фон (3 байти)
)

# Пакуємо у формат поля LXMF
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Надсилаємо повідомлення з цією іконкою
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# Можна також комбінувати з іншими полями, наприклад з вкладеннями:
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## Планувальник

Система планування задач:

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Виконується щодня опівночі
    pass
```

## Підписи

LXMFy надає параметри конфігурації для вбудованого в LXMF
криптографічного підписування та перевірки повідомлень:

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # Увімкнути перевірку підписів
    require_message_signatures=False      # Встановіть True, щоб відхиляти непідписані повідомлення
)
```

!!! note "Обробка підписів"

    LXMF автоматично виконує все криптографічне підписування та
    перевірку за допомогою ідентифікаторів RNS. `SignatureManager`
    LXMFy - це шар конфігурації, який:

    - Керує тим, чи застосовувати перевірку підписів
    - Визначає політику для непідписаних повідомлень (приймати або
      відхиляти)
    - Інтегрується з системою прав (наприклад, обхід перевірки для
      довірених користувачів)

Фактичні криптографічні операції виконує LXMF/RNS, а не LXMFy.

### Пісочниця Landlock LSM

На ядрах Linux з підтримкою Landlock (5.13+) LXMFy може обмежувати
доступ до файлової системи для процесу бота і для зовнішніх скриптових
коґів.

**Пісочниця процесу бота**

Коли `landlock_enabled=True` (типово) і бот не працює в `test_mode`,
бот викликає `apply_landlock_sandbox()` під час ініціалізації. Системні
каталоги доступні лише для читання; сховище бота, конфігурація, коґи,
конфігурація Reticulum і тимчасові шляхи лишаються доступними для
запису.

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# ключі status: landlock_kernel_supported, landlock_requested,
# landlock_auto_enabled, landlock_disabled_by_env, landlock_active
```

**Перевизначення через середовище**

- `LXMFY_LANDLOCK=0`: вимкнути Landlock навіть на підтримуваних ядрах
- `LXMFY_LANDLOCK=1`: спробувати Landlock на Linux незалежно від
  автовизначення
- не встановлено: слідувати `landlock_enabled` і автовизначенню ядра

**Пісочниця зовнішніх коґів**

Скриптові коґи використовують `external_cogs_sandbox_type`. У режимі
`auto` перевага надається Landlock, коли він доступний, бо він не
потребує зовнішніх інструментів. Повний список параметрів пісочниці
див. у посібнику [Створення ботів](creating-bots.md).

### Закріплення ідентифікатора

LXMFy підтримує опційне закріплення ідентифікатора для запобігання
імітації, якщо ідентифікатор ротовано або скомпрометовано. Коли
увімкнено, бот "закріплює" LXMF-адресу до першого побаченого публічного
ключа.

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### Методи SignatureManager

`SignatureManager` доступний як `bot.signature_manager`, коли
`signature_verification_enabled=True`:

- `should_verify_message(sender)`: визначає, чи слід перевіряти
  повідомлення від даного відправника
- `handle_unsigned_message(sender, message_hash)`: обробляє
  повідомлення без валідних підписів відповідно до політики

### Як працюють підписи LXMF

LXMF автоматично підписує всі вихідні повідомлення ідентифікатором RNS
відправника під час операції `pack()`. Коли повідомлення отримано, LXMF
перевіряє підписи і надає:

- `message.signature_validated`: булеве значення, що вказує, чи валідний
  підпис
- `message.unverified_reason`: код причини, якщо валідація не вдалася
  (наприклад, `SIGNATURE_INVALID`, `SOURCE_UNKNOWN`)

LXMFy використовує ці вбудовані властивості LXMF для застосування
політики підписів вашого бота.

## Доставка повідомлень

LXMFy надає розширені функції доставки повідомлень, включно з вузлами
поширення та автоматичними повторними спробами:

### Вузли поширення

Надсилайте повідомлення через конкретні вузли поширення для підвищення
надійності в мережі Reticulum:

``` python
# Налаштуйте вузол поширення один раз на рівні конфігурації/виконання
bot.set_propagation_node("<propagation_node_hash>")

# Надсилання з налаштованою поведінкою доставки
bot.send(
    destination_hash,
    "Message content"
)

# Хеш вузла поширення має бути валідним вузлом поширення LXMF
# у мережі Reticulum
```

### Автоматичні повторні спроби

Налаштуйте автоматичні повторні спроби для невдалих прямих доставок:

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # Повторювати пряму доставку до 5 разів
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# direct_delivery_retries типово дорівнює 3
# Логіка повторів автоматично обробляє зворотні виклики доставки
```

Система повторів відстежує спроби доставки для кожного отримувача і
автоматично повторює невдалі доставки. Успішні доставки скидають
лічильник повторів для цього отримувача.

### Персистентність повідомлень

Вихідні повідомлення можуть зберігатися на диску, щоб гарантувати їх
доставку навіть після перезапуску бота. Персистентність увімкнена
типово. Вихідна черга в пам'яті обмежена (`message_queue_size`, типово
50) і відкидає найстаріше повідомлення, коли заповнена. Невалідні хеші
отримувачів не відновлюються.

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

## Обробники повідомлень

LXMFy надає декоратори для обробки різних типів вхідних повідомлень:

### Обробник першого повідомлення

Обробляє перше повідомлення від кожного користувача:

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # Поверніть True, щоб зупинити подальшу обробку
```

### Загальний обробник повідомлень

Обробляє всі вхідні повідомлення до обробки команд:

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # Ваша логіка тут
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # Зупинити подальшу обробку

    return False  # Продовжити до обробки команд
```

Обробники повідомлень викликаються в такому порядку: 1. Обробник першого
повідомлення (якщо це перше повідомлення від цього відправника) 2.
Загальні обробники повідомлень (зареєстровані через `on_message()`) 3.
Обробка команд (якщо повідомлення починається з префікса команди)

## Reticulum Relay Chat (RRC)

Боти можуть приєднуватися до хабів [RRC](https://rrc.kc1awv.net/) через
RNS Link з конвертами CBOR. Пакет: `lxmfy.rrc`.

### Параметри BotConfig

- `rrc_enabled` (bool, типово `False`): підключати налаштовані хаби при
  запуску
- `rrc_hubs` (список hex-хешів): хеші отримувачів хабів
- `rrc_rooms` (список str): кімнати для автоматичного приєднання після
  WELCOME
- `rrc_nick` (str або None): нікнейм у HELLO і повідомленнях кімнат
- `rrc_dest_name` (str, типово `"rrc.hub"`): ім'я отримувача,
  використане для побудови адреси хаба
- `rrc_auto_reconnect` (bool, типово `True`): перепідключатися після
  втрати link
- `rrc_persist_sessions` (bool, типово `True`): зберігати хаби і
  кімнати між перезапусками
- `reticulum_config_dir` (str або None): каталог конфігурації
  Reticulum. Також задається через `LXMFY_RETICULUM_CONFIG_DIR`.
  Використовуйте ту саму конфігурацію, що в MeshChatX (часто
  `~/.reticulum`), щоб анонси хаба були видимі.

### Приклад

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

# API часу виконання
# bot.connect_rrc(hub_hash, rooms=["general"])
# bot.rrc.send_message("general", "hello")
# bot.rrc.send_notice("general", "notice")
# bot.rrc.send_action("general", "waves")
# bot.rrc.join("ops")
# bot.rrc.part("ops")
# bot.rrc.status()
# bot.disconnect_rrc()
```

### Експортовані типи

- `RRCClient`: сесія з одним хабом
- `RRCManager`: менеджер кількох хабів (`bot.rrc`)
- `RRCMessage`: корисне навантаження події кімнати (`kind`, `room`,
  `text`, `nick`, `src`, `mention`, ...)
- `RRC_VERSION`: константа версії дротового протоколу

Поширені події, що передаються обробникам `@bot.on_rrc`, включають
`status`, `welcome`, `joined`, `parted`, `msg`, `notice`, `action`,
`motd`, `error` і `rtt`.

# Шаблони

Фреймворк включає кілька готових до використання шаблонів ботів:

## EchoBot

Простий echo-бот, який повторює повідомлення:

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

Бот для нотаток зі сховищем JSON:

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

Бот-нагадувач зі сховищем SQLite:

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

RRC-бот для кімнат, який приєднується до налаштованих хабів і
відповідає на `@згадки`. Типово використовує хаб
`664fc0e8d2e448658e37bb3f34e6c88f`, кімнату `#general` і
`~/.reticulum`, коли доступний.

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

# Інструменти CLI

Фреймворк надає інструменти командного рядка для керування ботами:

``` bash
# Створити нового бота
lxmfy create mybot

# Створити бота з шаблону
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# Запустити шаблонного бота
lxmfy run echo
lxmfy run rrc

# Перевірити перевірку підписів повідомленням
lxmfy signatures test

# Увімкнути перевірку підписів
lxmfy signatures enable

# Вимкнути перевірку підписів
lxmfy signatures disable
```

# Обробка помилок

Перехоплюйте помилки завершення роботи та виконання навколо `bot.run()`:

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# Довідник модулів

Згенеровано з docstring у вихідному коді.

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
