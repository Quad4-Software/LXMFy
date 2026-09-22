# Kernkomponenten

## LXMFBot

Die Hauptklasse des Bots. Sie übernimmt das Routing von Nachrichten,
die Befehlsverarbeitung und die Verwaltung des Bot-Lebenszyklus.

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
    storage_type="json", # "json", "sqlite" oder "memory"
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
    reticulum_config_dir=None,  # oder LXMFY_RETICULUM_CONFIG_DIR / "~/.reticulum"
    rrc_enabled=False,
    rrc_hubs=[],
    rrc_rooms=[],
    rrc_nick=None,
    rrc_dest_name="rrc.hub",
    rrc_auto_reconnect=True,
    rrc_persist_sessions=True,
)
```

### Wichtige Methoden

- `get_landlock_status()`: Verfügbarkeit und Aktivierungsstatus der
  Landlock-LSM-Sandbox für den Bot-Prozess zurückgeben
- `run(delay=10)`: Hauptschleife des Bots starten
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)`:
  Nachricht an ein Ziel senden, optional mit eigenen LXMF-Feldern,
  Überschreibung der Stamp-Kosten und opportunistischem Versand
  (versucht Direktzustellung, greift bei Konfiguration sofort auf
  Propagation zurück).
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)`:
  Nachricht mit Anhang senden
- `command(name, description="No description provided", admin_only=False, threaded=False)`:
  Dekorator zur Registrierung von Befehlen. Mit `threaded=True` läuft
  der Befehls-Callback in einem separaten Thread. Befehle unterstützen
  typannotierte Argumente für automatische Konvertierung.
- `intent(name, examples)`: Dekorator zur Registrierung von
  NLP-Intent-Handlern.
- `nlp.export_model()`: Trainierte NLP-Modelldaten exportieren.
- `nlp.import_model(model_data)`: Zuvor exportierte NLP-Modelldaten
  importieren.
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)`:
  RNS-Link zu einem Ziel anfordern. Erlaubt eigenes `app_name` und
  `aspects` (Standard "lxmf" und "delivery").
- `on_link(callback)`: Handler für eingehende RNS-Links registrieren.
- `load_extension(name)`: Cog-Erweiterungsmodul anhand des Namens
  laden (z. B. "cogs.utility").
- `reload_extension(name)`: Cog-Erweiterungsmodul neu laden.
- `add_cog(cog_instance)`: Cog-Klasseninstanz zum Bot hinzufügen.
- `remove_cog(cog_name)`: Cog anhand seines Klassennamens entfernen.
- `on_first_message()`: Dekorator zur Verarbeitung erster Nachrichten
  von Benutzern
- `on_message()`: Dekorator zur Verarbeitung aller Nachrichten (wird
  vor der Befehlsverarbeitung aufgerufen)
- `on_reaction()`: Dekorator zur Verarbeitung eingehender Reaktionen.
  Handler erhalten `(sender, reaction)`, wobei reaction die Schlüssel
  `reaction_to`, `reaction_emoji` und `reaction_sender` enthält
- `react(destination, message_hash, reaction)`: Reaktion auf eine
  Nachricht über das LXMF-Feld `FIELD_REACTION` senden
- `validate()`: Validierungsprüfungen der Bot-Konfiguration ausführen
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)`:
  Als Client mit einem RRC-Hub verbinden
- `disconnect_rrc(hub_hash=None)`: Eine oder alle RRC-Hub-Sitzungen
  trennen
- `on_rrc(callback=None)`: Dekorator oder Handler-Registrierung für
  RRC-Ereignisse (`handler(event, client, payload)`)
- `rrc`: `RRCManager`-Instanz für Sitzungen mit mehreren Hubs

## Strukturierte Befehle über LXMF-Felder

Bots können Befehle empfangen, die über das LXMF-Feld
`FIELD_COMMANDS` (`0x09`) gesendet werden, und antworten automatisch
mit `FIELD_RESULTS` (`0x0A`). Damit sind strukturierte
Anfrage/Antwort-Workflows neben normalen Textbefehlen möglich.

Eingehende `FIELD_COMMANDS` werden geparst und über dieselbe
Befehlsregistrierung wie Textbefehle geroutet, mit gemeinsamen
Berechtigungsprüfungen, typannotiertem Argument-Parsing, Threading und
Middleware.

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields enthält das rohe LXMF-Felder-Dict
    # ctx.request_id wird automatisch gesetzt, wenn der Befehl eine enthielt
    ctx.reply("Bot is online")

# Senden eines strukturierten Befehls von einem anderen LXMF-Client:
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# Die Bot-Antwort enthält automatisch FIELD_RESULTS mit Antwort und request_id.
```

Um die Verarbeitung von Feldbefehlen zu deaktivieren,
`lxmf_commands_enabled=False` in `BotConfig` setzen.

## Reaktionen

Reaktionen werden als LXMF-Feld `FIELD_REACTION` (`0x40`) in einer
ansonsten leeren Nachricht übertragen. `pack_reaction` und
`unpack_reaction` erzeugen und parsen dieses Feld.

``` python
from lxmfy import pack_reaction, unpack_reaction

# Eine Reaktion auf eine Nachricht senden
bot.react(destination_hash, message_hash_hex, "thumbs up emoji")

# Reaktionen empfangen
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  - Hex-Hash der Zielnachricht
    # reaction["reaction_emoji"] - Reaktionstext (bis zu 16 Zeichen)
    # reaction["reaction_sender"] - Absender
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

Der Reaktionstext ist auf 16 druckbare Zeichen begrenzt. Das Rohfeld
bleibt in `ctx.fields` und `msg.fields` verfügbar (Kompatibilität).

## Speicher

Das Framework bietet drei Speicher-Backends:

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

storage = MemoryStorage() # Vollständig im Arbeitsspeicher
```

## Befehle

Befehlsregistrierung und -verarbeitung:

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Typannotierte Argumente

Befehle parsen und konvertieren Argumente automatisch anhand der
Typannotationen in der Callback-Funktion.

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## Hilfesystem

Das Framework enthält einen interaktiven Hilfe-Generator, der
kategorisierte Hilfemenüs auf Basis der Cog- und Command-Metadaten
erzeugt.

``` python
# Der help-Befehl wird automatisch registriert.
# Benutzer können '/help' oder '/help <command>' verwenden
```

### Befehle in separaten Threads

Für lang laufende oder blockierende Operationen, die nicht direkt mit
dem Reticulum Network Stack interagieren, können Befehle in einem
separaten Thread laufen, damit der Bot reaktionsfähig bleibt.

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # Läuft in einem separaten Thread
    ctx.reply("Long task completed!")
```

!!! warning "Threadsicherheit"

    Funktionen mit `threaded=True` **dürfen nicht** direkt mit dem
    Reticulum Network Stack (RNS) oder Komponenten interagieren, die
    auf `lxmfy.transport.py` aufbauen, da diese im Allgemeinen nicht
    threadsicher sind. Verwenden Sie `ctx.reply()`, um aus einem
    Threaded-Befehl heraus Nachrichten an den Benutzer zu senden.

## Ereignisse

Ereignissystem zur Verarbeitung verschiedener Bot-Ereignisse:

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Nachrichtenereignis verarbeiten
    pass
```

## Testen

Die Projekt-Tests umfassen Zuverlässigkeits- und Stresstest-Szenarien
in der Testsuite des Repositorys. Führen Sie sie mit dem Test-Runner
des Repositorys aus.

### Erweiterte Zuverlässigkeits-Testsuite

Das Framework enthält eine umfangreiche Suite automatisierter Tests
für raue Umgebungsbedingungen:

- **Manifold Testing**: Validiert die mathematische Topologie des
  NLP-Intent-Vektorraums.
- **Chaos Engineering**: Simuliert Bitrott, SD-Karten-Ausfall und
  Speicherkorruption.
- **Temporal Drift**: Prüft die Robustheit gegenüber
  Systemuhrsprüngen (±1 Jahr).
- **Leak Detection**: Langzeit-Überwachung von Speicher,
  Dateideskriptoren und Threads.

## Berechtigungen

Berechtigungssystem zur Zugriffskontrolle auf Bot-Funktionen:

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## Middleware

Middleware-System zur Verarbeitung von Nachrichten und Ereignissen:

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Vor der Befehlsausführung verarbeiten
    pass
```

## Anhänge

Unterstützung für das Senden von Dateien, Bildern und Audio:

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

## Icon-Darstellung (LXMF-Feld)

Sie können für Ihren Bot ein eigenes Icon setzen, das kompatible
LXMF-Clients anzeigen können. Dabei wird
`LXMF.FIELD_ICON_APPEARANCE` verwendet.

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Erforderlich für LXMF.FIELD_ICON_APPEARANCE

# Icon-Darstellung definieren
icon_data = IconAppearance(
    icon_name="smart_toy",  # Name aus Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # Weißer Vordergrund (3 Bytes)
    bg_color=b'\x4A\x90\xE2'   # Blauer Hintergrund (3 Bytes)
)

# In das LXMF-Feldformat packen
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Nachricht mit diesem Icon senden
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# Kann auch mit anderen Feldern kombiniert werden, z. B. Anhängen:
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## Scheduler

System zur Aufgabenplanung:

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Läuft täglich um Mitternacht
    pass
```

## Signaturen

LXMFy bietet Konfigurationsoptionen für die in LXMF eingebaute
kryptografische Nachrichtensignierung und -prüfung:

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # Signaturprüfung aktivieren
    require_message_signatures=False      # Auf True setzen, um unsignierte Nachrichten abzulehnen
)
```

!!! note "Verarbeitung von Signaturen"

    LXMF führt alle kryptografischen Signatur- und Prüfoperationen
    automatisch mit RNS-Identitäten aus. Der `SignatureManager` von
    LXMFy ist eine Konfigurationsschicht, die:

    - steuert, ob die Signaturprüfung erzwungen wird
    - die Richtlinie für unsignierte Nachrichten festlegt (annehmen
      oder ablehnen)
    - sich in das Berechtigungssystem integriert (z. B. Prüfung für
      vertrauenswürdige Benutzer umgehen)

Die eigentlichen kryptografischen Operationen führt LXMF/RNS aus,
nicht LXMFy.

### Landlock-LSM-Sandbox

Auf Linux-Kerneln mit Landlock-Unterstützung (5.13+) kann LXMFy den
Dateisystemzugriff für den Bot-Prozess und für externe Skript-Cogs
einschränken.

**Sandbox des Bot-Prozesses**

Wenn `landlock_enabled=True` (Standard) und der Bot nicht im
`test_mode` läuft, ruft der Bot `apply_landlock_sandbox()` während
der Initialisierung auf. Systemverzeichnisse sind nur lesbar.
Bot-Speicher, Konfiguration, Cogs, Reticulum-Konfiguration und
Temp-Pfade bleiben schreibbar.

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# status-Schlüssel: landlock_kernel_supported, landlock_requested,
# landlock_auto_enabled, landlock_disabled_by_env, landlock_active
```

**Überschreibung per Umgebungsvariable**

- `LXMFY_LANDLOCK=0`: Landlock auch auf unterstützten Kerneln
  deaktivieren
- `LXMFY_LANDLOCK=1`: Landlock unter Linux unabhängig von der
  Auto-Erkennung versuchen
- nicht gesetzt: `landlock_enabled` und Kernel-Auto-Erkennung folgen

**Sandbox für externe Cogs**

Skript-Cogs verwenden `external_cogs_sandbox_type`. Im Modus `auto`
wird Landlock bevorzugt, wenn verfügbar, da keine externen Werkzeuge
nötig sind. Die vollständige Liste der Sandbox-Optionen steht in der
Anleitung [Bots erstellen](creating-bots.md).

### Identitäts-Pinning

LXMFy unterstützt optionales Identitäts-Pinning, um
Identitätsdiebstahl zu verhindern, falls eine Identität rotiert oder
kompromittiert wird. Wenn aktiviert, "pinnt" der Bot eine
LXMF-Adresse an den zuerst gesehenen öffentlichen Schlüssel.

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### SignatureManager-Methoden

Der `SignatureManager` ist als `bot.signature_manager` verfügbar,
wenn `signature_verification_enabled=True`:

- `should_verify_message(sender)`: Feststellen, ob eine Nachricht des
  gegebenen Absenders geprüft werden soll
- `handle_unsigned_message(sender, message_hash)`: Nachrichten ohne
  gültige Signatur gemäß Richtlinie behandeln

### Wie LXMF-Signaturen funktionieren

LXMF signiert alle ausgehenden Nachrichten automatisch mit der
RNS-Identität des Absenders während der `pack()`-Operation. Beim
Empfang validiert LXMF die Signaturen und stellt bereit:

- `message.signature_validated`: Boolescher Wert, ob die Signatur
  gültig ist
- `message.unverified_reason`: Grundcode, falls die Validierung
  fehlschlug (z. B. `SIGNATURE_INVALID`, `SOURCE_UNKNOWN`)

LXMFy nutzt diese eingebauten LXMF-Eigenschaften, um die
Signaturrichtlinie Ihres Bots durchzusetzen.

## Nachrichtenzustellung

LXMFy bietet erweiterte Zustellfunktionen, darunter
Propagationsknoten und automatische Wiederholungen:

### Propagationsknoten

Nachrichten über bestimmte Propagationsknoten senden, um die
Zustellzuverlässigkeit im Reticulum-Netzwerk zu erhöhen:

``` python
# Propagationsknoten einmalig auf Konfigurations-/Laufzeitebene setzen
bot.set_propagation_node("<propagation_node_hash>")

# Mit konfiguriertem Zustellverhalten senden
bot.send(
    destination_hash,
    "Message content"
)

# Der Propagationsknoten-Hash sollte ein gültiger LXMF-Propagationsknoten
# im Reticulum-Netzwerk sein
```

### Automatische Wiederholungen

Automatische Wiederholungsversuche für fehlgeschlagene
Direktzustellungen konfigurieren:

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # Direktzustellung bis zu 5-mal wiederholen
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# direct_delivery_retries ist standardmäßig 3
# Die Wiederholungslogik verarbeitet Zustell-Callbacks automatisch
```

Das Wiederholungssystem verfolgt Zustellversuche pro Ziel und
wiederholt fehlgeschlagene Zustellungen automatisch. Erfolgreiche
Zustellungen setzen den Zähler für dieses Ziel zurück.

### Nachrichten-Persistenz

Ausgehende Nachrichten können auf die Festplatte persistiert werden,
damit sie auch nach einem Neustart des Bots zugestellt werden.
Persistenz ist standardmäßig aktiviert. Die Ausgangswarteschlange im
Speicher ist begrenzt (`message_queue_size`, Standard 50) und
verwirft bei Volllast die älteste Nachricht. Ungültige Ziel-Hashes
werden nicht wiederhergestellt.

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

## Nachrichten-Handler

LXMFy stellt Dekoratoren für verschiedene Arten eingehender
Nachrichten bereit:

### Handler für erste Nachrichten

Die erste Nachricht jedes Benutzers verarbeiten:

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # True zurückgeben, um die weitere Verarbeitung zu stoppen
```

### Allgemeiner Nachrichten-Handler

Alle eingehenden Nachrichten vor der Befehlsverarbeitung verarbeiten:

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # Eigene Logik hier
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # Weitere Verarbeitung stoppen

    return False  # Weiter zur Befehlsverarbeitung
```

Nachrichten-Handler werden in dieser Reihenfolge aufgerufen:
1. Handler für erste Nachrichten (wenn dies die erste Nachricht
dieses Absenders ist) 2. Allgemeine Nachrichten-Handler (registriert
mit `on_message()`) 3. Befehlsverarbeitung (wenn die Nachricht mit
dem Befehlspräfix beginnt)

## Reticulum Relay Chat (RRC)

Bots können [RRC](https://rrc.kc1awv.net/)-Hubs über RNS-Links mit
CBOR-Envelopes beitreten. Paket: `lxmfy.rrc`.

### BotConfig-Optionen

- `rrc_enabled` (bool, Standard `False`): Konfigurierte Hubs beim
  Start verbinden
- `rrc_hubs` (Liste von Hex-Hashes): Ziel-Hashes der Hubs
- `rrc_rooms` (Liste von Strings): Räume, die nach WELCOME automatisch
  betreten werden
- `rrc_nick` (String oder None): Nickname in HELLO und Raumnachrichten
- `rrc_dest_name` (String, Standard `"rrc.hub"`): Zielname zum Aufbau
  der Hub-Destination
- `rrc_auto_reconnect` (bool, Standard `True`): Nach Link-Verlust neu
  verbinden
- `rrc_persist_sessions` (bool, Standard `True`): Hubs und Räume über
  Neustarts hinweg speichern
- `reticulum_config_dir` (String oder None):
  Reticulum-Konfigurationsverzeichnis. Kann auch über
  `LXMFY_RETICULUM_CONFIG_DIR` gesetzt werden. Dieselbe Konfiguration
  wie MeshChatX verwenden (oft `~/.reticulum`), damit Hub-Announces
  sichtbar sind.

### Beispiel

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

# Laufzeit-API
# bot.connect_rrc(hub_hash, rooms=["general"])
# bot.rrc.send_message("general", "hello")
# bot.rrc.send_notice("general", "notice")
# bot.rrc.send_action("general", "waves")
# bot.rrc.join("ops")
# bot.rrc.part("ops")
# bot.rrc.status()
# bot.disconnect_rrc()
```

### Exportierte Typen

- `RRCClient`: Sitzung mit einem Hub
- `RRCManager`: Manager für mehrere Hubs (`bot.rrc`)
- `RRCMessage`: Payload eines Raumereignisses (`kind`, `room`,
  `text`, `nick`, `src`, `mention`, ...)
- `RRC_VERSION`: Konstante der Wire-Protokollversion

Übliche Ereignisse, die an `@bot.on_rrc`-Handler übergeben werden:
`status`, `welcome`, `joined`, `parted`, `msg`, `notice`, `action`,
`motd`, `error` und `rtt`.

# Vorlagen

Das Framework enthält mehrere einsatzbereite Bot-Vorlagen:

## EchoBot

Einfacher Echo-Bot, der Nachrichten wiederholt:

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

Notizen-Bot mit JSON-Speicher:

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

Erinnerungs-Bot mit SQLite-Speicher:

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

RRC-Raum-Bot, der konfigurierten Hubs beitritt und auf `@mentions`
antwortet. Standardmäßig Hub `664fc0e8d2e448658e37bb3f34e6c88f`,
Raum `#general` und `~/.reticulum`, falls verfügbar.

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

# CLI-Werkzeuge

Das Framework stellt Kommandozeilen-Werkzeuge für die Bot-Verwaltung
bereit:

``` bash
# Neuen Bot erstellen
lxmfy create mybot

# Bot aus Vorlage erstellen
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# Vorlagen-Bot ausführen
lxmfy run echo
lxmfy run rrc

# Signaturprüfung mit einer Nachricht testen
lxmfy signatures test

# Signaturprüfung aktivieren
lxmfy signatures enable

# Signaturprüfung deaktivieren
lxmfy signatures disable
```

# Fehlerbehandlung

Shutdown- und Laufzeitfehler rund um `bot.run()` abfangen:

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# Modulreferenz

Wird aus den Docstrings des Quellcodes generiert.

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
