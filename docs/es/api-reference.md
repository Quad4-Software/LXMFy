# Componentes principales

## LXMFBot

La clase principal del bot, que gestiona el enrutado de mensajes, el
procesamiento de comandos y el ciclo de vida del bot.

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
    storage_type="json", # "json", "sqlite" o "memory"
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
    reticulum_config_dir=None,  # o LXMFY_RETICULUM_CONFIG_DIR / "~/.reticulum"
    rrc_enabled=False,
    rrc_hubs=[],
    rrc_rooms=[],
    rrc_nick=None,
    rrc_dest_name="rrc.hub",
    rrc_auto_reconnect=True,
    rrc_persist_sessions=True,
)
```

### Métodos principales

- `get_landlock_status()`: devuelve la disponibilidad y el estado de
  activación del sandbox Landlock LSM del proceso del bot
- `run(delay=10)`: inicia el bucle principal del bot
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)`:
  envía un mensaje a un destino, opcionalmente con campos LXMF
  personalizados, coste de sello y envío oportunista (intenta la entrega
  directa y recurre a la propagación inmediatamente si está
  configurado).
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)`:
  envía un mensaje con un adjunto
- `command(name, description="No description provided", admin_only=False, threaded=False)`:
  decorador para registrar comandos. Define `threaded=True` para
  ejecutar el callback del comando en un hilo separado. Los comandos
  admiten argumentos con type hints para conversión automática.
- `intent(name, examples)`: decorador para registrar manejadores de
  intents NLP.
- `nlp.export_model()`: exporta los datos del modelo NLP entrenado.
- `nlp.import_model(model_data)`: importa datos de un modelo NLP
  exportado previamente.
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)`:
  solicita un link RNS a un destino. Permite `app_name` y `aspects`
  personalizados (por defecto "lxmf" y "delivery").
- `on_link(callback)`: registra un manejador para links RNS entrantes.
- `load_extension(name)`: carga un módulo de extensión cog por nombre
  (p. ej., "cogs.utility").
- `reload_extension(name)`: recarga un módulo de extensión cog.
- `add_cog(cog_instance)`: añade una instancia de clase cog al bot.
- `remove_cog(cog_name)`: elimina un cog del bot por su nombre de clase.
- `on_first_message()`: decorador para manejar los primeros mensajes de
  los usuarios
- `on_message()`: decorador para manejar todos los mensajes (se llama
  antes del procesamiento de comandos)
- `on_reaction()`: decorador para manejar reacciones entrantes. Los
  manejadores reciben `(sender, reaction)`, donde reaction lleva las
  claves `reaction_to`, `reaction_emoji` y `reaction_sender`
- `react(destination, message_hash, reaction)`: envía una reacción a un
  mensaje mediante el campo LXMF `FIELD_REACTION`
- `validate()`: ejecuta comprobaciones de validación sobre la
  configuración del bot
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)`:
  conecta a un hub RRC como cliente
- `disconnect_rrc(hub_hash=None)`: desconecta una o todas las sesiones
  de hub RRC
- `on_rrc(callback=None)`: decorador o registro de manejador para
  eventos RRC (`handler(event, client, payload)`)
- `rrc`: instancia de `RRCManager` para sesiones multi-hub

## Comandos estructurados mediante campos LXMF

Los bots pueden recibir comandos enviados mediante el campo LXMF
`FIELD_COMMANDS` (`0x09`) y responder automáticamente con
`FIELD_RESULTS` (`0x0A`). Esto permite flujos de petición/respuesta
estructurados junto a los comandos de texto normales.

Los `FIELD_COMMANDS` entrantes se analizan y se enrutan por el mismo
registro de comandos que los de texto, compartiendo las comprobaciones
de permisos, el parseo de argumentos tipados, los hilos y el middleware.

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields contiene el dict de campos LXMF en bruto
    # ctx.request_id se establece automáticamente si el comando lo incluía
    ctx.reply("Bot is online")

# Envío de un comando estructurado desde otro cliente LXMF:
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# La respuesta del bot incluye automáticamente FIELD_RESULTS con la respuesta y el request_id.
```

Para desactivar el procesamiento de comandos de campo, define
`lxmf_commands_enabled=False` en `BotConfig`.

## Reacciones

Las reacciones viajan como el campo LXMF `FIELD_REACTION` (`0x40`) en un
mensaje por lo demás vacío. `pack_reaction` y `unpack_reaction`
construyen y analizan ese campo.

``` python
from lxmfy import pack_reaction, unpack_reaction

# Enviar una reacción a un mensaje
bot.react(destination_hash, message_hash_hex, "thumbs up emoji")

# Recibir reacciones
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  - hash en hex del mensaje objetivo
    # reaction["reaction_emoji"] - texto de la reacción (hasta 16 caracteres)
    # reaction["reaction_sender"] - remitente
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

El texto de la reacción está limitado a 16 caracteres imprimibles. El
campo en bruto sigue disponible en `ctx.fields` y `msg.fields` por
compatibilidad.

## Almacenamiento

El framework ofrece tres backends de almacenamiento:

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

storage = MemoryStorage() # Íntegramente en memoria
```

## Comandos

Registro y manejo de comandos:

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Argumentos con type hints

Los comandos analizan y convierten automáticamente los argumentos según
los type hints de la función callback.

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## Sistema de ayuda

El framework incluye un generador interactivo de ayuda que ofrece menús
categorizados basados en los metadatos de Cog y Command.

``` python
# El comando de ayuda se registra automáticamente.
# Los usuarios pueden usar '/help' o '/help <command>'
```

### Comandos en hilos

Para operaciones de larga duración o bloqueantes que no interactúan
directamente con el Reticulum Network Stack, puedes ejecutar comandos en
un hilo separado para que el bot siga respondiendo.

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # Esto se ejecuta en un hilo separado
    ctx.reply("Long task completed!")
```

!!! warning "Seguridad en hilos"

    Las funciones marcadas como `threaded=True` **no deben** interactuar
    directamente con el Reticulum Network Stack (RNS) ni con ningún
    componente que dependa de `lxmfy.transport.py`, ya que en general no
    son seguros para hilos. Usa `ctx.reply()` para enviar mensajes al
    usuario desde un comando en hilo.

## Eventos

Sistema de eventos para manejar los distintos eventos del bot:

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Manejar el evento de mensaje
    pass
```

## Testing

Los tests del proyecto incluyen escenarios de fiabilidad y estrés en la
suite de tests del repositorio. Usa el runner de tests del repositorio
para ejecutarlos.

### Suite avanzada de fiabilidad

El framework incluye una amplia suite de tests automatizados para
entornos difíciles:

- **Manifold Testing**: valida la topología matemática del espacio
  vectorial de intents NLP.
- **Chaos Engineering**: simula degradación de bits, fallo de tarjeta SD
  y corrupción del almacenamiento.
- **Temporal Drift**: verifica la resiliencia ante saltos del reloj del
  sistema (±1 año).
- **Leak Detection**: seguimiento a largo plazo de memoria, descriptores
  de archivo e hilos.

## Permisos

Sistema de permisos para controlar el acceso a las funciones del bot:

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## Middleware

Sistema de middleware para procesar mensajes y eventos:

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Procesar antes de la ejecución del comando
    pass
```

## Adjuntos

Soporte para enviar archivos, imágenes y audio:

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

## Icono de apariencia (campo LXMF)

Puedes definir un icono personalizado para tu bot que los clientes LXMF
compatibles pueden mostrar. Usa el campo `LXMF.FIELD_ICON_APPEARANCE`.

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Necesario para LXMF.FIELD_ICON_APPEARANCE

# Definir la apariencia del icono
icon_data = IconAppearance(
    icon_name="smart_toy",  # Nombre de Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # Primer plano blanco (3 bytes)
    bg_color=b'\x4A\x90\xE2'   # Fondo azul (3 bytes)
)

# Empaquetarlo en el formato de campo LXMF
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Enviar un mensaje con este icono
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# También puedes combinarlo con otros campos, como adjuntos:
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## Scheduler

Sistema de planificación de tareas:

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Se ejecuta cada día a medianoche
    pass
```

## Firmas

LXMFy ofrece opciones de configuración para la firma y verificación
criptográfica de mensajes integrada en LXMF:

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # Activar la comprobación de firmas
    require_message_signatures=False      # Poner a True para rechazar mensajes sin firmar
)
```

!!! note "Gestión de firmas"

    LXMF gestiona automáticamente toda la firma y verificación
    criptográfica usando identidades RNS. El `SignatureManager` de
    LXMFy es una capa de configuración que:

    - Controla si se aplica la verificación de firmas
    - Determina la política para mensajes sin firmar (aceptar o
      rechazar)
    - Se integra con el sistema de permisos (p. ej., omitir la
      verificación para usuarios de confianza)

Las operaciones criptográficas reales las realiza LXMF/RNS, no LXMFy.

### Sandbox Landlock LSM

En kernels de Linux con soporte de Landlock (5.13+), LXMFy puede
restringir el acceso al sistema de archivos del proceso del bot y de los
cogs de scripts externos.

**Sandbox del proceso del bot**

Cuando `landlock_enabled=True` (por defecto) y no se ejecuta en
`test_mode`, el bot llama a `apply_landlock_sandbox()` durante la
inicialización. Los directorios del sistema quedan de solo lectura. El
almacenamiento del bot, la configuración, los cogs, la configuración de
Reticulum y las rutas temporales siguen siendo escribibles.

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# claves de status: landlock_kernel_supported, landlock_requested,
# landlock_auto_enabled, landlock_disabled_by_env, landlock_active
```

**Anulación por entorno**

- `LXMFY_LANDLOCK=0`: desactiva Landlock incluso en kernels compatibles
- `LXMFY_LANDLOCK=1`: intenta Landlock en Linux con independencia de la
  autodetección
- sin definir: sigue `landlock_enabled` y la autodetección del kernel

**Sandbox de cogs externos**

Los cogs de scripts usan `external_cogs_sandbox_type`. En modo `auto` se
prefiere Landlock cuando está disponible porque no requiere herramientas
externas. Consulta la guía [Creación de bots](creating-bots.md) para la
lista completa de opciones de sandbox.

### Identity pinning

LXMFy admite identity pinning opcional para evitar la suplantación si
una identidad rota o se ve comprometida. Cuando está activado, el bot
"fija" una dirección LXMF a la primera clave pública vista.

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### Métodos de SignatureManager

El `SignatureManager` está disponible como `bot.signature_manager`
cuando `signature_verification_enabled=True`:

- `should_verify_message(sender)`: determina si un mensaje del remitente
  dado debe verificarse
- `handle_unsigned_message(sender, message_hash)`: gestiona los mensajes
  sin firmas válidas según la política

### Cómo funcionan las firmas LXMF

LXMF firma automáticamente todos los mensajes salientes usando la
identidad RNS del remitente durante la operación `pack()`. Al recibir
mensajes, LXMF valida las firmas y proporciona:

- `message.signature_validated`: booleano que indica si la firma es
  válida
- `message.unverified_reason`: código de motivo si la validación falló
  (p. ej., `SIGNATURE_INVALID`, `SOURCE_UNKNOWN`)

LXMFy usa estas propiedades integradas de LXMF para aplicar la política
de firmas de tu bot.

## Entrega de mensajes

LXMFy ofrece funciones avanzadas de entrega de mensajes, incluidos nodos
de propagación y reintentos automáticos:

### Nodos de propagación

Envía mensajes a través de nodos de propagación concretos para mejorar
la fiabilidad en la red Reticulum:

``` python
# Configurar el nodo de propagación una vez a nivel de config/ejecución
bot.set_propagation_node("<propagation_node_hash>")

# Enviar usando el comportamiento de entrega configurado
bot.send(
    destination_hash,
    "Message content"
)

# El hash del nodo de propagación debe ser un nodo de propagación LXMF
# válido en la red Reticulum
```

### Reintentos automáticos

Configura los reintentos automáticos para las entregas directas
fallidas:

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # Reintentar la entrega directa hasta 5 veces
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# direct_delivery_retries por defecto es 3
# La lógica de reintento gestiona automáticamente los callbacks de entrega
```

El sistema de reintentos registra los intentos de entrega por destino y
reintenta automáticamente las entregas fallidas. Las entregas correctas
reinician el contador de reintentos de ese destino.

### Persistencia de mensajes

Los mensajes salientes se pueden persistir en disco para garantizar su
entrega incluso tras un reinicio del bot. La persistencia está activada
por defecto. La cola de salida en memoria está limitada
(`message_queue_size`, 50 por defecto) y descarta el mensaje más antiguo
cuando se llena. Los hashes de destino inválidos no se restauran.

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

## Manejadores de mensajes

LXMFy ofrece decoradores para manejar distintos tipos de mensajes
entrantes:

### Manejador del primer mensaje

Maneja el primer mensaje de cada usuario:

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # Devolver True para detener el procesamiento
```

### Manejador general de mensajes

Maneja todos los mensajes entrantes antes del procesamiento de comandos:

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # Lógica personalizada aquí
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # Detener el procesamiento

    return False  # Continuar al procesamiento de comandos
```

Los manejadores de mensajes se llaman en este orden: 1. Manejador del
primer mensaje (si es el primer mensaje de este remitente) 2.
Manejadores generales de mensajes (registrados con `on_message()`) 3.
Procesamiento de comandos (si el mensaje empieza por el prefijo de
comandos)

## Reticulum Relay Chat (RRC)

Los bots pueden unirse a hubs de [RRC](https://rrc.kc1awv.net/) sobre
RNS Links con sobres CBOR. Paquete: `lxmfy.rrc`.

### Opciones de BotConfig

- `rrc_enabled` (bool, por defecto `False`): conectar los hubs
  configurados al arrancar
- `rrc_hubs` (lista de hashes en hex): hashes de destino de los hubs
- `rrc_rooms` (lista de str): salas a las que unirse tras WELCOME
- `rrc_nick` (str o None): nick en HELLO y mensajes de sala
- `rrc_dest_name` (str, por defecto `"rrc.hub"`): nombre de destino
  usado para construir el destino del hub
- `rrc_auto_reconnect` (bool, por defecto `True`): reconectar tras la
  pérdida del link
- `rrc_persist_sessions` (bool, por defecto `True`): persistir hubs y
  salas entre reinicios
- `reticulum_config_dir` (str o None): directorio de configuración de
  Reticulum. También se define con `LXMFY_RETICULUM_CONFIG_DIR`. Usa la
  misma configuración que MeshChatX (a menudo `~/.reticulum`) para que
  los anuncios del hub sean visibles.

### Ejemplo

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

# API en tiempo de ejecución
# bot.connect_rrc(hub_hash, rooms=["general"])
# bot.rrc.send_message("general", "hello")
# bot.rrc.send_notice("general", "notice")
# bot.rrc.send_action("general", "waves")
# bot.rrc.join("ops")
# bot.rrc.part("ops")
# bot.rrc.status()
# bot.disconnect_rrc()
```

### Tipos exportados

- `RRCClient`: sesión de un solo hub
- `RRCManager`: gestor multi-hub (`bot.rrc`)
- `RRCMessage`: payload de evento de sala (`kind`, `room`, `text`,
  `nick`, `src`, `mention`, ...)
- `RRC_VERSION`: constante de versión del protocolo de red

Los eventos habituales que reciben los manejadores de `@bot.on_rrc`
incluyen `status`, `welcome`, `joined`, `parted`, `msg`, `notice`,
`action`, `motd`, `error` y `rtt`.

# Plantillas

El framework incluye varias plantillas de bot listas para usar:

## EchoBot

Bot eco sencillo que repite los mensajes:

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

Bot de notas con almacenamiento JSON:

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

Bot de recordatorios con almacenamiento SQLite:

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

Bot de sala RRC que se une a los hubs configurados y responde a las
`@menciones`. Usa por defecto el hub
`664fc0e8d2e448658e37bb3f34e6c88f`, la sala `#general` y `~/.reticulum`
cuando está disponible.

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

# Herramientas CLI

El framework proporciona herramientas de línea de comandos para la
gestión de bots:

``` bash
# Crear un bot nuevo
lxmfy create mybot

# Crear un bot a partir de una plantilla
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# Ejecutar un bot de plantilla
lxmfy run echo
lxmfy run rrc

# Probar la verificación de firmas con un mensaje
lxmfy signatures test

# Activar la verificación de firmas
lxmfy signatures enable

# Desactivar la verificación de firmas
lxmfy signatures disable
```

# Manejo de errores

Captura los fallos de apagado y de ejecución alrededor de `bot.run()`:

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# Referencia de módulos

Generada a partir de los docstrings del código fuente.

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
