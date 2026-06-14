# 🎬 Discord OBS Overlay

Affiche en temps réel les images, vidéos et textes envoyés via Discord directement dans OBS Studio, avec avatar et pseudo de l'expéditeur.

---

## 📋 Prérequis

- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/install/)
- Un serveur Discord avec les droits administrateur
- OBS Studio

---

## 📥 Installation

### 1. Clone le projet

```bash
git clone https://github.com/AliB2002/LiveChat.git
cd LiveChat
```

### 2. Crée le fichier `.env`

```bash
cp .env.example .env
nano .env
```

Remplis les valeurs :

```env
DISCORD_TOKEN=TON_TOKEN_ICI
SECRET_KEY=UNE_CLE_ALEATOIRE_ICI
PUBLIC_URL=http://TON_IP_OU_DOMAINE:5000
GUILD_ID=TON_GUILD_ID_ICI
```

| Variable | Description | Exemple |
|---|---|---|
| `DISCORD_TOKEN` | Token du bot Discord | `MTExN...` |
| `SECRET_KEY` | Clé secrète Flask aléatoire | `a3f8c2e1b74d9...` |
| `PUBLIC_URL` | URL publique de ton serveur | `http://178.170.116.94:5000` |
| `GUILD_ID` | ID de ton serveur Discord | `987654321012345678` |

> Pour générer une SECRET_KEY solide :
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

### 3. Lance le projet

```bash
docker compose up -d --build
```

Tu dois voir dans les logs :
```
✅ Bot connecté : TonBot#1234
✅ Commandes synchronisées sur le serveur XXXXXXXXX
```

Pour voir les logs en direct :
```bash
docker compose logs -f
```

---

## 🤖 Créer le bot Discord

1. Va sur [discord.com/developers/applications](https://discord.com/developers/applications)
2. Clique sur **"New Application"** → donne un nom
3. Va dans **"Bot"** → clique sur **"Reset Token"** → copie le token
4. Dans **"Bot"**, active ces intents :
   - ✅ `Message Content Intent`
   - ✅ `Server Members Intent`
   - ✅ `Presence Intent`
   - ✅ `Message Content Intent` (nécessaire pour lire le contenu des messages)
   - ✅ `Add Reactions` (nécessaire pour ajouter des réactions aux messages)
5. Va dans **"OAuth2" → "URL Generator"**
6. Coche les scopes :
   - ✅ `bot`
   - ✅ `applications.commands`
7. Coche les permissions Bot :
   - ✅ `Send Messages`
   - ✅ `View Channels`
   - ✅ `Add Reactions` (pour les confirmations de détection automatique)
8. Copie l'URL générée en bas → ouvre-la dans ton navigateur → invite le bot sur ton serveur

---

## 🆔 Récupérer le Guild ID

1. Dans Discord, va dans **Paramètres → Avancés** → active le **Mode développeur**
2. Fais un **clic droit sur l'icône de ton serveur** dans la liste à gauche
3. Clique sur **"Copier l'identifiant"**
4. Colle cette valeur dans le `.env` pour `GUILD_ID`

---

## 🎮 Commandes Discord

| Commande | Paramètres | Description |
|---|---|---|
| `/stop` | — | Stoppe l'élément en cours et passe au suivant |
| `/dispo` | — | Vérifie si le serveur overlay est opérationnel |
| `/obs` | — | Affiche le lien à coller dans OBS |

### ⚡ Détection automatique

**Le bot détecte maintenant automatiquement les messages contenant des vidéos, images, audio ou texte et les envoie directement à l'overlay OBS !**

- ✅ Envoyez une vidéo (MP4, MOV, WEBM) → affichage automatique dans OBS
- ✅ Envoyez une image (PNG, JPG, GIF, WEBP) → affichage automatique dans OBS
- ✅ Envoyez un fichier audio (MP3, WAV, OGG) → lecture automatique dans OBS
- ✅ Envoyez du texte → affichage automatique dans OBS
- ✅ Le bot ajoute une réaction **✅** pour confirmer la prise en compte
- ✅ Si erreur, le bot ajoute une réaction **❌**

### Formats supportés

| Type | Extensions |
|---|---|
| Images | PNG, JPG, JPEG, GIF, WEBP |
| Vidéos | MP4, MOV, WEBM |
| Audio | MP3, WAV, OGG |

---

## 📺 Configurer OBS Studio

1. Dans OBS, clique sur **"+"** dans les Sources → **"Navigateur"**
2. Remplis les champs :
   - **URL** : `http://TON_IP:5000/overlay`
   - **Largeur** : `1920`
   - **Hauteur** : `1080`
   - ✅ Coche **"Arrière-plan de la page transparent"**
3. Dans **"CSS personnalisé"**, colle :
   ```css
   body { background-color: rgba(0,0,0,0) !important; }
   ```
4. Clique sur **OK**

### Activer le son dans OBS

1. Fais **clic droit** sur la source navigateur → **"Interagir"**
2. Clique sur le bouton **"🔊 Cliquer pour activer le son"**
3. Le son est maintenant actif pour toute la session OBS

> ⚠️ Cette étape est à refaire à chaque redémarrage d'OBS.

---

## 🗂️ Structure du projet

```
LiveChat/
├── .env                  ← Variables d'environnement (ne pas commit)
├── .env.example          ← Modèle du fichier .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── supervisord.conf
├── requirements.txt
├── server.py             ← Serveur Flask + SocketIO + FFmpeg
├── bot.py                ← Bot Discord (commandes slash)
└── templates/
    └── overlay.html      ← Page OBS transparente
```

---

## 🔧 Commandes utiles

```bash
# Démarrer
docker compose up -d --build

# Arrêter
docker compose down

# Voir les logs en direct
docker compose logs -f

```

---

