# Componentes principais

## LXMFBot

A classe principal do bot, que trata do encaminhamento de mensagens, do
processamento de comandos e da gestão do ciclo de vida do bot.

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
    reticulum_config_dir=None,  # ou LXMFY_RETICULUM_CONFIG_DIR / "~/.reticulum"
    rrc_enabled=False,
    rrc_hubs=[],
    rrc_rooms=[],
    rrc_nick=None,
    rrc_dest_name="rrc.hub",
    rrc_auto_reconnect=True,
    rrc_persist_sessions=True,
)
```

### Métodos principais

- `get_landlock_status()`: devolve a disponibilidade e o estado de
  ativação da sandbox Landlock LSM para o processo do bot
- `run(delay=10)`: inicia o ciclo principal do bot
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)`:
  envia uma mensagem para um destino, opcionalmente com campos LXMF
  personalizados, substituição do custo de stamp e envio oportunista
  (tenta a entrega direta e recorre imediatamente à propagação, se
  configurado).
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)`:
  envia uma mensagem com um anexo
- `command(name, description="No description provided", admin_only=False, threaded=False)`:
  decorador para registar comandos. Defina `threaded=True` para executar
  o callback do comando numa thread separada. Os comandos suportam
  argumentos anotados por tipo para conversão automática.
- `intent(name, examples)`: decorador para registar manipuladores de
  intents NLP.
- `nlp.export_model()`: exporta os dados do modelo NLP treinado.
- `nlp.import_model(model_data)`: importa dados de modelo NLP
  previamente exportados.
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)`:
  pede um link RNS para um destino. Permite `app_name` e `aspects`
  personalizados (predefinição "lxmf" e "delivery").
- `on_link(callback)`: regista um manipulador para links RNS recebidos.
- `load_extension(name)`: carrega um módulo de extensão cog pelo nome
  (ex.: "cogs.utility").
- `reload_extension(name)`: recarrega um módulo de extensão cog.
- `add_cog(cog_instance)`: adiciona uma instância de classe cog ao bot.
- `remove_cog(cog_name)`: remove um cog do bot pelo nome da classe.
- `on_first_message()`: decorador para tratar as primeiras mensagens dos
  utilizadores
- `on_message()`: decorador para tratar todas as mensagens (chamado
  antes do processamento de comandos)
- `on_reaction()`: decorador para tratar reações recebidas. Os
  manipuladores recebem `(sender, reaction)`, onde reaction traz as
  chaves `reaction_to`, `reaction_emoji` e `reaction_sender`
- `react(destination, message_hash, reaction)`: envia uma reação a uma
  mensagem através do campo LXMF `FIELD_REACTION`
- `validate()`: executa verificações de validação na configuração do bot
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)`:
  liga a um hub RRC como cliente
- `disconnect_rrc(hub_hash=None)`: desliga uma ou todas as sessões de
  hub RRC
- `on_rrc(callback=None)`: decorador ou registo de manipulador para
  eventos RRC (`handler(event, client, payload)`)
- `rrc`: instância `RRCManager` para sessões multi-hub

## Comandos estruturados via campos LXMF

Os bots podem receber comandos enviados via `FIELD_COMMANDS` (`0x09`)
do LXMF e responder automaticamente com `FIELD_RESULTS` (`0x0A`). Isto
permite fluxos estruturados de pedido/resposta em paralelo com os
comandos de texto normais.

Os `FIELD_COMMANDS` recebidos são analisados e encaminhados pelo mesmo
registo de comandos dos comandos de texto, partilhando verificações de
permissões, parsing de argumentos anotados por tipo, threading e
middleware.

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields contém o dicionário de campos LXMF em bruto
    # ctx.request_id é definido automaticamente se o comando incluir um
    ctx.reply("Bot is online")

# Enviar um comando estruturado a partir de outro cliente LXMF:
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# A resposta do bot inclui automaticamente FIELD_RESULTS com a resposta e o request_id.
```

Para desativar o processamento de comandos por campos, defina
`lxmf_commands_enabled=False` no `BotConfig`.

## Reações

As reações viajam no campo LXMF `FIELD_REACTION` (`0x40`) de uma
mensagem por outro lado vazia. `pack_reaction` e `unpack_reaction`
constroem e analisam esse campo.

``` python
from lxmfy import pack_reaction, unpack_reaction

# Enviar uma reação a uma mensagem
bot.react(destination_hash, message_hash_hex, "thumbs up emoji")

# Receber reações
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  - hash hex da mensagem alvo
    # reaction["reaction_emoji"] - texto da reação (até 16 caracteres)
    # reaction["reaction_sender"] - remetente
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

O texto da reação está limitado a 16 caracteres imprimíveis. O campo em
bruto continua disponível em `ctx.fields` e `msg.fields` para
compatibilidade.

## Armazenamento

O framework fornece três backends de armazenamento:

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

storage = MemoryStorage() # Inteiramente em memória
```

## Comandos

Registo e tratamento de comandos:

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Argumentos anotados por tipo

Os comandos analisam e convertem automaticamente os argumentos com base
nas anotações de tipo da função de callback.

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## Sistema de ajuda

O framework inclui um gerador de ajuda interativo que produz menus de
ajuda categorizados com base nos metadados de Cog e Command.

``` python
# O comando help é registado automaticamente.
# Os utilizadores podem usar '/help' ou '/help <command>'
```

### Comandos em thread

Para operações demoradas ou bloqueantes que não interagem diretamente
com a Reticulum Network Stack, pode executar comandos numa thread
separada para manter o bot responsivo.

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # Isto corre numa thread separada
    ctx.reply("Long task completed!")
```

!!! warning "Segurança de threads"

    Funções marcadas como `threaded=True` **não devem** interagir
    diretamente com a Reticulum Network Stack (RNS) nem com componentes
    que dependam de `lxmfy.transport.py`, pois geralmente não são
    thread-safe. Use `ctx.reply()` para enviar mensagens ao utilizador a
    partir de um comando em thread.

## Eventos

Sistema de eventos para tratar vários eventos do bot:

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Tratar o evento de mensagem
    pass
```

## Testes

Os testes do projeto incluem cenários de fiabilidade e de stress na
suite de testes do repositório. Use o runner de testes do repositório
para os executar.

### Suite avançada de fiabilidade

O framework inclui uma suite extensa de testes automatizados para
ambientes hostis:

- **Testes de manifold**: valida a topologia matemática do espaço
  vetorial de intents NLP.
- **Engenharia do caos**: simula bit-rot, falha de cartão SD e corrupção
  de armazenamento.
- **Desvio temporal**: verifica a resiliência a saltos do relógio do
  sistema (±1 ano).
- **Deteção de fugas**: acompanhamento a longo prazo de memória,
  descritores de ficheiros e threads.

## Permissões

Sistema de permissões para controlar o acesso às funcionalidades do bot:

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## Middleware

Sistema de middleware para processar mensagens e eventos:

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Processar antes da execução do comando
    pass
```

## Anexos

Suporte para envio de ficheiros, imagens e áudio:

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

## Aparência de ícone (campo LXMF)

Pode definir um ícone personalizado para o bot que clientes LXMF
compatíveis conseguem apresentar. Usa o `LXMF.FIELD_ICON_APPEARANCE`.

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Necessário para LXMF.FIELD_ICON_APPEARANCE

# Definir a aparência do ícone
icon_data = IconAppearance(
    icon_name="smart_toy",  # Nome dos Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # Primeiro plano branco (3 bytes)
    bg_color=b'\x4A\x90\xE2'   # Fundo azul (3 bytes)
)

# Empacotar no formato de campo LXMF
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Enviar uma mensagem com este ícone
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# Também pode combiná-lo com outros campos, como anexos:
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## Agendador

Sistema de agendamento de tarefas:

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Executar diariamente à meia-noite
    pass
```

## Assinaturas

O LXMFy fornece opções de configuração para a assinatura e verificação
criptográfica de mensagens integrada no LXMF:

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # Ativar a verificação de assinaturas
    require_message_signatures=False      # Definir como True para rejeitar mensagens não assinadas
)
```

!!! note "Gestão de assinaturas"

    O LXMF trata automaticamente de toda a assinatura e verificação
    criptográfica usando identidades RNS. O `SignatureManager` do LXMFy
    é uma camada de configuração que:

    - Controla se a verificação de assinaturas é aplicada
    - Determina a política para mensagens não assinadas (aceitar ou
      rejeitar)
    - Integra com o sistema de permissões (ex.: ignorar a verificação
      para utilizadores de confiança)

As operações criptográficas propriamente ditas são executadas pelo
LXMF/RNS, não pelo LXMFy.

### Sandbox Landlock LSM

Em kernels Linux com suporte a Landlock (5.13+), o LXMFy pode restringir
o acesso ao sistema de ficheiros para o processo do bot e para cogs de
scripts externos.

**Sandbox do processo do bot**

Quando `landlock_enabled=True` (predefinição) e não está em `test_mode`,
o bot chama `apply_landlock_sandbox()` durante a inicialização. Os
diretórios do sistema ficam só de leitura; o armazenamento do bot, a
configuração, os cogs, a configuração Reticulum e os caminhos temporários
mantêm-se graváveis.

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# chaves de status: landlock_kernel_supported, landlock_requested,
# landlock_auto_enabled, landlock_disabled_by_env, landlock_active
```

**Sobreposição por variável de ambiente**

- `LXMFY_LANDLOCK=0`: desativa o Landlock mesmo em kernels suportados
- `LXMFY_LANDLOCK=1`: tenta o Landlock em Linux independentemente da
  deteção automática
- não definida: segue `landlock_enabled` e a deteção automática do
  kernel

**Sandbox dos cogs externos**

Os cogs de script usam `external_cogs_sandbox_type`. No modo `auto`, o
Landlock é preferido quando disponível por não precisar de ferramentas
externas. Consulte o guia [Criar bots](creating-bots.md) para a lista
completa de opções de sandbox.

### Fixação de identidade

O LXMFy suporta fixação de identidade opcional (identity pinning) para
evitar personificação se uma identidade for rodada ou comprometida.
Quando ativa, o bot "fixa" um endereço LXMF à primeira chave pública
vista.

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### Métodos do SignatureManager

O `SignatureManager` está disponível como `bot.signature_manager` quando
`signature_verification_enabled=True`:

- `should_verify_message(sender)`: determina se uma mensagem do
  remetente dado deve ser verificada
- `handle_unsigned_message(sender, message_hash)`: trata mensagens sem
  assinatura válida conforme a política

### Como funcionam as assinaturas LXMF

O LXMF assina automaticamente todas as mensagens enviadas usando a
identidade RNS do remetente durante a operação `pack()`. Quando as
mensagens são recebidas, o LXMF valida as assinaturas e fornece:

- `message.signature_validated`: booleano que indica se a assinatura é
  válida
- `message.unverified_reason`: código de motivo se a validação falhar
  (ex.: `SIGNATURE_INVALID`, `SOURCE_UNKNOWN`)

O LXMFy usa estas propriedades integradas do LXMF para aplicar a
política de assinaturas do bot.

## Entrega de mensagens

O LXMFy fornece funcionalidades avançadas de entrega de mensagens,
incluindo nós de propagação e repetições automáticas:

### Nós de propagação

Envie mensagens através de nós de propagação específicos para maior
fiabilidade na rede Reticulum:

``` python
# Configurar o nó de propagação uma vez, ao nível da configuração/execução
bot.set_propagation_node("<propagation_node_hash>")

# Enviar usando o comportamento de entrega configurado
bot.send(
    destination_hash,
    "Message content"
)

# O hash do nó de propagação deve ser um nó de propagação LXMF válido
# na rede Reticulum
```

### Repetições automáticas

Configure tentativas automáticas de repetição para entregas diretas
falhadas:

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # Repetir a entrega direta até 5 vezes
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# O direct_delivery_retries predefinido é 3
# A lógica de repetição trata automaticamente dos callbacks de entrega
```

O sistema de repetição acompanha as tentativas de entrega por destino e
repete automaticamente as entregas falhadas. Entregas bem-sucedidas
repõem o contador de repetições desse destino.

### Persistência de mensagens

As mensagens de saída podem ser persistidas em disco para garantir a
entrega mesmo após um reinício do bot. A persistência está ativa por
predefinição. A fila de saída em memória é limitada
(`message_queue_size`, predefinição 50) e descarta a mensagem mais
antiga quando cheia. Hashes de destino inválidos não são restaurados.

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

## Manipuladores de mensagens

O LXMFy fornece decoradores para tratar diferentes tipos de mensagens
recebidas:

### Manipulador da primeira mensagem

Trate a primeira mensagem de cada utilizador:

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # Devolver True para parar o processamento
```

### Manipulador geral de mensagens

Trate todas as mensagens recebidas antes do processamento de comandos:

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # Lógica personalizada aqui
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # Parar o processamento

    return False  # Continuar para o processamento de comandos
```

Os manipuladores de mensagens são chamados nesta ordem: 1. Manipulador
da primeira mensagem (se for a primeira mensagem deste remetente)
2. Manipuladores gerais de mensagens (registados com `on_message()`)
3. Processamento de comandos (se a mensagem começar com o prefixo de
comando)

## Reticulum Relay Chat (RRC)

Os bots podem entrar em hubs [RRC](https://rrc.kc1awv.net/) através de
RNS Links com envelopes CBOR. Pacote: `lxmfy.rrc`.

### Opções do BotConfig

- `rrc_enabled` (bool, predefinição `False`): ligar aos hubs
  configurados no arranque
- `rrc_hubs` (lista de hashes hex): hashes de destino dos hubs
- `rrc_rooms` (lista de str): salas a entrar automaticamente após
  WELCOME
- `rrc_nick` (str ou None): nickname no HELLO e nas mensagens de sala
- `rrc_dest_name` (str, predefinição `"rrc.hub"`): nome de destino usado
  para construir o destino do hub
- `rrc_auto_reconnect` (bool, predefinição `True`): religar após perda
  do link
- `rrc_persist_sessions` (bool, predefinição `True`): persistir hubs e
  salas entre reinícios
- `reticulum_config_dir` (str ou None): diretório de configuração
  Reticulum. Também definível via `LXMFY_RETICULUM_CONFIG_DIR`. Use a
  mesma configuração do MeshChatX (frequentemente `~/.reticulum`) para
  os anúncios do hub serem visíveis.

### Exemplo

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

# API em tempo de execução
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

- `RRCClient`: sessão de um único hub
- `RRCManager`: gestor multi-hub (`bot.rrc`)
- `RRCMessage`: payload de evento de sala (`kind`, `room`, `text`,
  `nick`, `src`, `mention`, ...)
- `RRC_VERSION`: constante da versão do protocolo de rede

Os eventos comuns passados aos manipuladores `@bot.on_rrc` incluem
`status`, `welcome`, `joined`, `parted`, `msg`, `notice`, `action`,
`motd`, `error` e `rtt`.

# Templates

O framework inclui vários templates de bot prontos a usar:

## EchoBot

Bot de eco simples que repete as mensagens:

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

Bot de notas com armazenamento JSON:

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

Bot de lembretes com armazenamento SQLite:

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

Bot de sala RRC que entra nos hubs configurados e responde a
`@menções`. Usa por predefinição o hub
`664fc0e8d2e448658e37bb3f34e6c88f`, a sala `#general` e `~/.reticulum`
quando disponível.

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

# Ferramentas CLI

O framework fornece ferramentas de linha de comandos para gestão do bot:

``` bash
# Criar um novo bot
lxmfy create mybot

# Criar um bot a partir de um template
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# Executar um bot de template
lxmfy run echo
lxmfy run rrc

# Testar a verificação de assinaturas com uma mensagem
lxmfy signatures test

# Ativar a verificação de assinaturas
lxmfy signatures enable

# Desativar a verificação de assinaturas
lxmfy signatures disable
```

# Tratamento de erros

Capture falhas de encerramento e de execução à volta de `bot.run()`:

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# Referência de módulos

Gerado a partir das docstrings do código-fonte.

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
