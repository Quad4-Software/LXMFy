# Composants principaux

## LXMFBot

La classe principale du bot, qui gère le routage des messages, le
traitement des commandes et le cycle de vie du bot.

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
    storage_type="json", # "json", "sqlite", ou "memory"
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

### Méthodes principales

- `get_landlock_status()` : renvoie la disponibilité et l'état
  d'activation de la sandbox Landlock LSM pour le processus du bot
- `run(delay=10)` : démarre la boucle principale du bot
- `send(destination, message, title="Reply", lxmf_fields=None, stamp_cost=None, opportunistic=None)` :
  envoie un message à une destination, avec en option des champs LXMF
  personnalisés, une surcharge du coût de tampon, et un envoi
  opportuniste (essaie la livraison directe, puis bascule
  immédiatement sur la propagation si configuré).
- `send_with_attachment(destination, message, attachment, title="Reply", stamp_cost=None, opportunistic=None)` :
  envoie un message avec une pièce jointe
- `command(name, description="No description provided", admin_only=False, threaded=False)` :
  décorateur pour enregistrer des commandes. Définissez
  `threaded=True` pour exécuter le callback de la commande dans un
  thread séparé. Les commandes prennent en charge les arguments avec
  annotations de type pour la conversion automatique.
- `intent(name, examples)` : décorateur pour enregistrer des
  gestionnaires d'intentions NLP.
- `nlp.export_model()` : exporte les données du modèle NLP entraîné.
- `nlp.import_model(model_data)` : importe des données de modèle NLP
  précédemment exportées.
- `request_link(destination_hash, callback=None, app_name="lxmf", *aspects)` :
  demande un lien RNS vers une destination. Permet un `app_name` et des
  `aspects` personnalisés (par défaut "lxmf" et "delivery").
- `on_link(callback)` : enregistre un gestionnaire pour les liens RNS
  entrants.
- `load_extension(name)` : charge un module d'extension cog par nom
  (par ex. "cogs.utility").
- `reload_extension(name)` : recharge un module d'extension cog.
- `add_cog(cog_instance)` : ajoute une instance de classe cog au bot.
- `remove_cog(cog_name)` : retire un cog du bot par son nom de classe.
- `on_first_message()` : décorateur pour gérer les premiers messages
  des utilisateurs
- `on_message()` : décorateur pour gérer tous les messages (appelé
  avant le traitement des commandes)
- `on_reaction()` : décorateur pour gérer les réactions entrantes. Les
  gestionnaires reçoivent `(sender, reaction)` où reaction porte les
  clés `reaction_to`, `reaction_emoji` et `reaction_sender`
- `react(destination, message_hash, reaction)` : envoie une réaction à
  un message via le champ LXMF `FIELD_REACTION`
- `validate()` : exécute les vérifications de validation sur la
  configuration du bot
- `connect_rrc(hub_hash, rooms=None, nick=None, dest_name=None, auto_reconnect=None)` :
  se connecte à un hub RRC en tant que client
- `disconnect_rrc(hub_hash=None)` : déconnecte une ou toutes les
  sessions de hubs RRC
- `on_rrc(callback=None)` : décorateur ou enregistrement de
  gestionnaire pour les événements RRC (`handler(event, client,
  payload)`)
- `rrc` : instance `RRCManager` pour les sessions multi-hubs

## Commandes structurées via les champs LXMF

Les bots peuvent recevoir des commandes envoyées via le champ LXMF
`FIELD_COMMANDS` (`0x09`) et répondre automatiquement avec
`FIELD_RESULTS` (`0x0A`). Cela permet des flux requête/réponse
structurés en parallèle des commandes textuelles normales.

Les `FIELD_COMMANDS` entrants sont analysés et routés dans le même
registre de commandes que les commandes textuelles, en partageant les
vérifications de permissions, l'analyse des arguments annotés, le
threading et le middleware.

``` python
from lxmfy import LXMFBot, FIELD_COMMANDS, FIELD_RESULTS, pack_result, unpack_commands

bot = LXMFBot(name="FieldBot")

@bot.command(name="status", description="Return bot status")
def status_cmd(ctx):
    # ctx.fields contient le dict brut des champs LXMF
    # ctx.request_id est renseigné automatiquement si la commande en incluait un
    ctx.reply("Bot is online")

# Envoi d'une commande structurée depuis un autre client LXMF :
# lxm.fields[FIELD_COMMANDS] = {"command": "status", "args": [], "request_id": "abc123"}
# router.handle_outbound(lxm)

# La réponse du bot inclut automatiquement FIELD_RESULTS avec la réponse et le request_id.
```

Pour désactiver le traitement des commandes par champs, définissez
`lxmf_commands_enabled=False` dans `BotConfig`.

## Réactions

Les réactions voyagent dans le champ LXMF `FIELD_REACTION` (`0x40`)
d'un message par ailleurs vide. `pack_reaction` et `unpack_reaction`
construisent et analysent ce champ.

``` python
from lxmfy import pack_reaction, unpack_reaction

# Envoyer une réaction à un message
bot.react(destination_hash, message_hash_hex, "thumbs up emoji")

# Recevoir des réactions
@bot.on_reaction()
def on_reaction(sender, reaction):
    # reaction["reaction_to"]  - hachage hex du message cible
    # reaction["reaction_emoji"] - texte de la réaction (16 caractères max)
    # reaction["reaction_sender"] - expéditeur
    print(f"{sender} reacted {reaction['reaction_emoji']} to {reaction['reaction_to']}")
    return True
```

Le texte de réaction est limité à 16 caractères imprimables. Le champ
brut reste disponible dans `ctx.fields` et `msg.fields` pour la
compatibilité.

## Stockage

Le framework fournit trois backends de stockage :

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

storage = MemoryStorage() # Entièrement en mémoire
```

## Commandes

Enregistrement et traitement des commandes :

``` python
@bot.command(name="hello", description="Says hello")
def hello(ctx):
    ctx.reply(f"Hello {ctx.sender}!")
```

### Arguments avec annotations de type

Les commandes analysent et convertissent automatiquement les arguments
d'après les annotations de type de la fonction de callback.

``` python
@bot.command(name="add", description="Adds two numbers")
def add(ctx, a: int, b: int):
    result = a + b
    ctx.reply(f"The result is {result}")
```

## Système d'aide

Le framework inclut un générateur d'aide interactif qui produit des
menus d'aide catégorisés à partir des métadonnées des cogs et des
commandes.

``` python
# La commande help est enregistrée automatiquement.
# Les utilisateurs peuvent utiliser '/help' ou '/help <command>'
```

### Commandes en thread

Pour les opérations longues ou bloquantes qui n'interagissent pas
directement avec le Reticulum Network Stack, vous pouvez exécuter les
commandes dans un thread séparé pour garder le bot réactif.

``` python
import time

@bot.command(name="long_task", description="Performs a long-running task in a separate thread", threaded=True)
def long_task_command(ctx):
    ctx.reply("Starting a long task... please wait.")
    time.sleep(10) # S'exécute dans un thread séparé
    ctx.reply("Long task completed!")
```

!!! warning "Sécurité des threads"

    Les fonctions marquées `threaded=True` **ne doivent pas** interagir
    directement avec le Reticulum Network Stack (RNS) ni avec les
    composants qui dépendent de `lxmfy.transport.py`, car ils ne sont
    généralement pas thread-safe. Utilisez `ctx.reply()` pour renvoyer
    des messages à l'utilisateur depuis une commande en thread.

## Événements

Système d'événements pour gérer les différents événements du bot :

``` python
@bot.events.on("message_received", EventPriority.HIGHEST)
def handle_message(event):
    # Traiter l'événement message
    pass
```

## Tests

Les tests du projet incluent des scénarios de fiabilité et de charge
dans la suite de tests du dépôt. Utilisez le lanceur de tests du dépôt
pour les exécuter.

### Suite avancée de fiabilité

Le framework inclut une suite étendue de tests automatisés pour les
environnements difficiles :

- **Manifold Testing** : valide la topologie mathématique de l'espace
  vectoriel des intentions NLP.
- **Chaos Engineering** : simule le bit rot, les pannes de carte SD et
  la corruption du stockage.
- **Temporal Drift** : vérifie la résilience face aux sauts d'horloge
  système (±1 an).
- **Leak Detection** : suivi à long terme de la mémoire, des
  descripteurs de fichiers et des threads.

## Permissions

Système de permissions pour contrôler l'accès aux fonctions du bot :

``` python
from lxmfy import DefaultPerms

@bot.command(name="admin", description="Admin command", admin_only=True)
def admin_command(ctx):
    if ctx.is_admin:
        ctx.reply("Admin command executed")
```

## Middleware

Système de middleware pour traiter les messages et les événements :

``` python
@bot.middleware.register(MiddlewareType.PRE_COMMAND)
def pre_command_middleware(ctx):
    # Traitement avant l'exécution de la commande
    pass
```

## Pièces jointes

Prise en charge de l'envoi de fichiers, d'images et d'audio :

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

## Apparence de l'icône (champ LXMF)

Vous pouvez définir une icône personnalisée pour votre bot, que les
clients LXMF compatibles peuvent afficher. Elle utilise le champ
`LXMF.FIELD_ICON_APPEARANCE`.

``` python
from lxmfy import IconAppearance, pack_icon_appearance_field
import LXMF # Requis pour LXMF.FIELD_ICON_APPEARANCE

# Définir l'apparence de l'icône
icon_data = IconAppearance(
    icon_name="smart_toy",  # Nom depuis Material Symbols
    fg_color=b'\xFF\xFF\xFF',  # Premier plan blanc (3 octets)
    bg_color=b'\x4A\x90\xE2'   # Arrière-plan bleu (3 octets)
)

# L'empaqueter au format du champ LXMF
icon_lxmf_field = pack_icon_appearance_field(icon_data)

# Envoyer un message avec cette icône
bot.send(
    destination_hash_str,
    "Hello from your friendly bot!",
    title="Bot Message",
    lxmf_fields=icon_lxmf_field
)

# Vous pouvez aussi la combiner avec d'autres champs, comme des pièces jointes :
# attachment_field = pack_attachment(some_attachment)
# combined_fields = {**icon_lxmf_field, **attachment_field}
# bot.send(destination, "Message with icon and attachment", lxmf_fields=combined_fields)
```

## Planificateur

Système de planification de tâches :

``` python
@bot.scheduler.schedule(name="daily_task", cron_expr="0 0 * * *")
def daily_task():
    # Exécution quotidienne à minuit
    pass
```

## Signatures

LXMFy fournit des options de configuration pour la signature et la
vérification cryptographiques intégrées de LXMF :

``` python
from lxmfy import LXMFBot

bot = LXMFBot(
    name="SecureBot",
    signature_verification_enabled=True,  # Activer les vérifications de signature
    require_message_signatures=False      # Mettre True pour rejeter les messages non signés
)
```

!!! note "Gestion des signatures"

    LXMF gère automatiquement toute la signature et la vérification
    cryptographiques via les identités RNS. Le `SignatureManager` de
    LXMFy est une couche de configuration qui :

    - Contrôle si la vérification des signatures est appliquée
    - Détermine la politique pour les messages non signés (accepter ou
      rejeter)
    - S'intègre au système de permissions (par ex. contourner la
      vérification pour les utilisateurs de confiance)

Les opérations cryptographiques réelles sont effectuées par LXMF/RNS,
pas par LXMFy.

### Sandbox Landlock LSM

Sur les noyaux Linux prenant en charge Landlock (5.13+), LXMFy peut
restreindre l'accès au système de fichiers pour le processus du bot et
pour les cogs en scripts externes.

**Sandbox du processus du bot**

Quand `landlock_enabled=True` (défaut) et hors `test_mode`, le bot
appelle `apply_landlock_sandbox()` pendant l'initialisation. Les
répertoires système sont en lecture seule. Le stockage du bot, la
config, les cogs, la config Reticulum et les chemins temporaires
restent inscriptibles.

``` python
bot = LXMFBot(
    name="SecureBot",
    landlock_enabled=True,
)

status = bot.get_landlock_status()
# clés de status : landlock_kernel_supported, landlock_requested,
# landlock_auto_enabled, landlock_disabled_by_env, landlock_active
```

**Surcharge par variable d'environnement**

- `LXMFY_LANDLOCK=0` : désactive Landlock même sur les noyaux
  compatibles
- `LXMFY_LANDLOCK=1` : tente Landlock sous Linux quelle que soit
  l'auto-détection
- non définie : suit `landlock_enabled` et l'auto-détection du noyau

**Sandbox des cogs externes**

Les cogs en scripts utilisent `external_cogs_sandbox_type`. En mode
`auto`, Landlock est préféré quand il est disponible car il ne requiert
aucun outil externe. Voir le guide [Création de
bots](creating-bots.md) pour la liste complète des options de sandbox.

### Épinglage d'identité

LXMFy prend en charge un épinglage d'identité optionnel pour empêcher
l'usurpation si une identité est remplacée ou compromise. Quand il est
activé, le bot "épingle" une adresse LXMF à la première clé publique
vue.

``` python
bot = LXMFBot(
    identity_pinning_enabled=True
)
```

### Méthodes de SignatureManager

Le `SignatureManager` est disponible via `bot.signature_manager` quand
`signature_verification_enabled=True` :

- `should_verify_message(sender)` : détermine si un message d'un
  expéditeur donné doit être vérifié
- `handle_unsigned_message(sender, message_hash)` : traite les messages
  sans signature valide selon la politique

### Fonctionnement des signatures LXMF

LXMF signe automatiquement tous les messages sortants avec l'identité
RNS de l'expéditeur pendant l'opération `pack()`. À la réception, LXMF
valide les signatures et fournit :

- `message.signature_validated` : booléen indiquant si la signature est
  valide
- `message.unverified_reason` : code de raison si la validation a
  échoué (par ex. `SIGNATURE_INVALID`, `SOURCE_UNKNOWN`)

LXMFy utilise ces propriétés LXMF intégrées pour appliquer la politique
de signature de votre bot.

## Livraison des messages

LXMFy fournit des fonctions de livraison de messages avancées, dont les
nœuds de propagation et les réessais automatiques :

### Nœuds de propagation

Envoyez des messages via des nœuds de propagation précis pour une
meilleure fiabilité sur le réseau Reticulum :

``` python
# Configurer le nœud de propagation une fois, au niveau config/runtime
bot.set_propagation_node("<propagation_node_hash>")

# Envoyer avec le comportement de livraison configuré
bot.send(
    destination_hash,
    "Message content"
)

# Le hachage du nœud de propagation doit être un nœud de propagation LXMF valide
# sur le réseau Reticulum
```

### Réessais automatiques

Configurez les réessais automatiques pour les livraisons directes
échouées :

``` python
bot = LXMFBot(
    name="ReliableBot",
    direct_delivery_retries=5,  # Réessayer la livraison directe jusqu'à 5 fois
    propagation_fallback_enabled=True
)

bot.send(destination_hash, "Important message")

# direct_delivery_retries vaut 3 par défaut
# La logique de réessai gère automatiquement les callbacks de livraison
```

Le système de réessais suit les tentatives de livraison par destination
et réessaie automatiquement les livraisons échouées. Les livraisons
réussies remettent le compteur de réessais à zéro pour cette
destination.

### Persistance des messages

Les messages sortants peuvent être persistés sur disque pour garantir
leur livraison même après un redémarrage du bot. La persistance est
activée par défaut. La file sortante en mémoire est bornée
(`message_queue_size`, défaut 50) et supprime le plus ancien message
quand elle est pleine. Les hachages de destination invalides ne sont
pas restaurés.

``` python
bot = LXMFBot(
    message_persistence_enabled=True,
    message_queue_size=50,
)
```

## Gestionnaires de messages

LXMFy fournit des décorateurs pour gérer différents types de messages
entrants :

### Gestionnaire de premier message

Gérez le premier message de chaque utilisateur :

``` python
@bot.on_first_message()
def welcome_user(sender, message):
    content = message.content.decode("utf-8")
    bot.send(sender, f"Welcome! You said: {content}")
    return True  # Renvoyer True pour arrêter le traitement
```

### Gestionnaire de messages général

Gérez tous les messages entrants avant le traitement des commandes :

``` python
@bot.on_message()
def handle_all_messages(sender, message):
    content = message.content.decode("utf-8").strip()

    # Logique personnalisée ici
    if content.startswith("echo:"):
        bot.send(sender, content[5:])
        return True  # Arrêter le traitement

    return False  # Continuer vers le traitement des commandes
```

Les gestionnaires de messages sont appelés dans cet ordre : 1.
Gestionnaire de premier message (si c'est le premier message de cet
expéditeur) 2. Gestionnaires de messages généraux (enregistrés avec
`on_message()`) 3. Traitement des commandes (si le message commence par
le préfixe de commande)

## Reticulum Relay Chat (RRC)

Les bots peuvent rejoindre des hubs [RRC](https://rrc.kc1awv.net/) via
des liens RNS avec des enveloppes CBOR. Paquet : `lxmfy.rrc`.

### Options de BotConfig

- `rrc_enabled` (bool, défaut `False`) : connecte les hubs configurés
  au démarrage
- `rrc_hubs` (liste de hachages hex) : hachages de destination des hubs
- `rrc_rooms` (liste de str) : salons à rejoindre automatiquement après
  WELCOME
- `rrc_nick` (str ou None) : pseudo dans HELLO et les messages de salon
- `rrc_dest_name` (str, défaut `"rrc.hub"`) : nom de destination utilisé
  pour construire la destination du hub
- `rrc_auto_reconnect` (bool, défaut `True`) : reconnecte après une
  perte de lien
- `rrc_persist_sessions` (bool, défaut `True`) : persiste les hubs et
  les salons entre les redémarrages
- `reticulum_config_dir` (str ou None) : répertoire de config
  Reticulum. Définissable aussi via `LXMFY_RETICULUM_CONFIG_DIR`.
  Utilisez la même config que MeshChatX (souvent `~/.reticulum`) pour
  que les annonces des hubs soient visibles.

### Exemple

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

# API d'exécution
# bot.connect_rrc(hub_hash, rooms=["general"])
# bot.rrc.send_message("general", "hello")
# bot.rrc.send_notice("general", "notice")
# bot.rrc.send_action("general", "waves")
# bot.rrc.join("ops")
# bot.rrc.part("ops")
# bot.rrc.status()
# bot.disconnect_rrc()
```

### Types exportés

- `RRCClient` : session mono-hub
- `RRCManager` : gestionnaire multi-hubs (`bot.rrc`)
- `RRCMessage` : charge utile d'événement de salon (`kind`, `room`,
  `text`, `nick`, `src`, `mention`, ...)
- `RRC_VERSION` : constante de version du protocole réseau

Les événements courants passés aux gestionnaires `@bot.on_rrc`
incluent `status`, `welcome`, `joined`, `parted`, `msg`, `notice`,
`action`, `motd`, `error` et `rtt`.

# Modèles

Le framework inclut plusieurs modèles de bots prêts à l'emploi :

## EchoBot

Bot echo simple qui répète les messages :

``` python
from lxmfy.templates import EchoBot

bot = EchoBot()
bot.run()
```

## NoteBot

Bot de prise de notes avec stockage JSON :

``` python
from lxmfy.templates import NoteBot

bot = NoteBot()
bot.run()
```

## ReminderBot

Bot de rappels avec stockage SQLite :

``` python
from lxmfy.templates import ReminderBot

bot = ReminderBot()
bot.run()
```

## RRCBot

Bot de salon RRC qui rejoint les hubs configurés et répond aux
`@mentions`. Utilise par défaut le hub
`664fc0e8d2e448658e37bb3f34e6c88f`, le salon `#general` et
`~/.reticulum` quand il est disponible.

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

# Outils CLI

Le framework fournit des outils en ligne de commande pour la gestion
des bots :

``` bash
# Créer un nouveau bot
lxmfy create mybot

# Créer un bot depuis un modèle
lxmfy create --template echo mybot
lxmfy create --template rrc my_rrc_bot

# Exécuter un bot à partir d'un modèle
lxmfy run echo
lxmfy run rrc

# Tester la vérification des signatures avec un message
lxmfy signatures test

# Activer la vérification des signatures
lxmfy signatures enable

# Désactiver la vérification des signatures
lxmfy signatures disable
```

# Gestion des erreurs

Capturez les erreurs d'arrêt et d'exécution autour de `bot.run()` :

``` python
try:
    bot.run()
except KeyboardInterrupt:
    bot.cleanup()
except Exception as e:
    logger.error(f"Error running bot: {str(e)}")
```

# Référence des modules

Généré à partir des docstrings des sources.

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
