# Liens entre routes du Back et routes/tables de la BDD

## Configuration pour tester

Lancer d'abord la BDD, puis le back.

```bash
# terminal 1
cd GestionBDD
python app.py

# terminal 2
cd MultiBlindTest_Back
export BDD_API_URL=http://127.0.0.1:5001
python Flask/app.py
```

Le back appelle la BDD via `Library/bdd_client.py`.
Les routes métier récentes utilisent surtout la route BDD générique `POST /mbt/sql/execute` pour lire/écrire dans les tables SQLite.

## Route de vérification ajoutée

```txt
GET /routes/health
GET /routes/links
```

`GET /routes/links` renvoie en JSON le mapping complet : route Back, route BDD utilisée, tables touchées et exemple de body.

## Mapping principal à utiliser côté front

| Fonction | Route Back à tester | Route BDD utilisée | Tables BDD liées |
|---|---|---|---|
| Inscription | `POST /register` ou `POST /mbt/register` | `POST /mbt/register` | `Users`, `Settings`, `Profils`, `Rank`, `Subscriptions` |
| Connexion | `POST /mbt/login` ou `POST /login/user` | `POST /mbt/login` | `Users` |
| Liste campagne | `GET /campaign/levels?campaign_id=1` | `POST /mbt/sql/execute` | `Campaign`, `CampaignLevels`, `Levels`, `Levels_Etat`, `Victory` |
| Détail niveau campagne | `GET /campaign/levels/<level_id>?campaign_id=1` | `POST /mbt/sql/execute` | `Levels`, `Levels_Etat`, `Music`, `Victory` |
| Compléter niveau campagne | `POST /campaign/levels/<level_id>/complete` | `POST /mbt/sql/execute` | `Levels_Etat`, `CampaignLevels` |
| Créer niveau custom | `POST /creator/levels` | `POST /mbt/sql/script` puis `POST /mbt/sql/execute` | `LevelsCustom` |
| Mes niveaux custom | `GET /creator/levels` | `POST /mbt/sql/execute` | `LevelsCustom` |
| Détail niveau custom | `GET /creator/levels/<level_id>` | `POST /mbt/sql/execute` | `LevelsCustom`, `LevelTracks` |
| Ajouter lien YouTube | `POST /creator/levels/<level_id>/tracks` | `POST /mbt/sql/execute` | `LevelTracks` |
| Démarrer partie | `POST /levels/<level_id>/start` | `POST /mbt/sql/script` puis `POST /mbt/sql/execute` | `GameSessions`, `GameSessionFoundTracks`, `Levels`, `Levels_Etat`, `Music` |
| État partie | `GET /levels/<level_id>/game-state` | `POST /mbt/sql/execute` | `GameSessions`, `GameSessionFoundTracks`, `Levels`, `Music` |
| Répondre | `POST /levels/<level_id>/answer` | `POST /mbt/sql/execute` | `GameSessions`, `GameSessionFoundTracks`, `Music` |
| Hint | `POST /levels/<level_id>/hint` | `POST /mbt/sql/execute` | `GameSessions`, `Levels` |
| Fin de partie | `POST /levels/<level_id>/end-game` | `POST /mbt/sql/execute` | `GameSessions`, `Victory`, `Profils`, `Levels_Etat`, `CampaignLevels` |
| Ancienne liste niveaux publics | `GET /mbt/levels` | `GET /mbt/levels` | `Levels`, `Community_Level`, `Music` |
| Anciennes musiques niveau | `GET /mbt/music/<level_id>` | `GET /mbt/music/<level_id>` | `Music` |

## Parcours de test conseillé

1. `POST /register` pour créer un utilisateur.
2. `POST /mbt/login` pour récupérer un token.
3. Ajouter le token dans les headers : `Authorization: Bearer <access_token>`.
4. `GET /campaign/levels?campaign_id=1` pour voir les niveaux et leur état.
5. `POST /levels/<level_id>/start` pour démarrer la partie.
6. `GET /levels/<level_id>/game-state` pour récupérer les musiques trouvées/non trouvées, vies et temps.
7. `POST /levels/<level_id>/answer` pour tester une réponse.
8. `POST /levels/<level_id>/hint` pour tester l'indice.
9. `POST /levels/<level_id>/end-game` pour finir la partie et écrire les résultats dans la BDD.
10. `GET /campaign/levels?campaign_id=1` pour vérifier étoiles/progression.

## Bodies d'exemple

### Inscription

```json
{
  "name": "testuser",
  "nom": "Test",
  "email": "test@example.com",
  "password": "Password123",
  "age": 18
}
```

### Connexion

```json
{
  "name": "testuser",
  "password": "Password123"
}
```

### Level Creator - créer un niveau

```json
{
  "title": "Mon Blind Test",
  "artist_tag": "Pop",
  "theme": "NEON_PINK"
}
```

### Level Creator - ajouter YouTube

```json
{
  "youtube_url": "https://youtube.com/watch?v=...",
  "start_point": 30,
  "duration": 12,
  "difficulty": 1
}
```

### Jeu - réponse

```json
{
  "guess": "Titre musique",
  "time_left": 42
}
```

### Jeu - fin de partie

```json
{
  "campaign_id": 1,
  "time_left": 20
}
```

## Ce que j'ai relié

- Ajout de `controllers/route_links_controller.py`.
- Enregistrement du controller dans `Flask/app.py`.
- Ajout de `GET /routes/links` pour visualiser les correspondances Back -> BDD directement depuis l'API.
- Ajout de ce document pour tester les routes dans l'ordre.
- Les anciennes routes `/mbt/...`, `/play/<id>`, `/end_game` sont conservées pour ne pas casser ton front actuel.
