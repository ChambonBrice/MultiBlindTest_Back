# Corrections syntaxe SQL / routes Postman

## Problème réglé

Le token Back -> BDD fonctionne. Les erreurs restantes venaient surtout de requêtes SQL qui utilisaient des colonnes qui n'existent pas dans ta BDD.

Exemples corrigés :

- `cl.LevelsID` remplacé par `cl.LevelID`
- `l.nb_music` remplacé par `COUNT(m.ID) AS nb_music`
- `l.timer` remplacé par une valeur par défaut `60 AS timer`
- `l.lives` remplacé par une valeur par défaut `3 AS lives`
- `Victory.UserID` évité car la table `Victory` actuelle ne contient pas `UserID`

## Tables réellement prises en compte

### Levels
Colonnes utilisées :
- `ID`
- `stats`
- `hint`
- `LevelName`
- `Difficulty`

### CampaignLevels
Colonnes utilisées :
- `ID`
- `CampaignID`
- `LevelID`
- `Theme`
- `Score`

### Music
Colonnes utilisées :
- `ID`
- `LevelsID`
- `Name`
- `PATH`

## Fichiers modifiés

### Back

- `MultiBlindTest_Back/Library/campagne.py`
  - Correction des colonnes de campagne.
  - Calcul du nombre de musiques avec `COUNT(Music.ID)`.
  - Déblocage du niveau suivant avec `CampaignLevels.LevelID`.

- `MultiBlindTest_Back/controllers/campaign_controller.py`
  - Remplacement de la lecture de `Victory.UserID`.
  - Ajout d'une table `UserLevelResults` pour stocker les résultats joueur/niveau.

- `MultiBlindTest_Back/controllers/game_controller.py`
  - Correction de la lecture d'un niveau.
  - Ajout de valeurs par défaut pour `timer` et `lives`.
  - Calcul de `nb_music` depuis la table `Music`.

- `MultiBlindTest_Back/Library/victory.py`
  - Correction de l'enregistrement des résultats.
  - Utilisation de `UserLevelResults` au lieu d'une colonne inexistante `Victory.UserID`.

- `MultiBlindTest_Back/Library/level.py`
  - Suppression de la dépendance à `Levels.lives`.
  - Utilisation de `Music.LevelsID`.

- `MultiBlindTest_Back/Flask/app.py`
  - Correction du login pour récupérer un vrai `Users.ID` numérique.
  - Correction de la route `/profile`.

### BDD

- `GestionBDD/app.py`
  - Correction du retour `id` dans `/mbt/login`.
  - Correction du retour `id` dans `/mbt/users`.
  - Correction de `/mbt/music/<level_id>` pour ne plus utiliser des colonnes inexistantes.

## Ordre de test Postman conseillé

1. `POST /mbt/register`
2. `POST /mbt/login`
3. Copier le `access_token` utilisateur dans Postman.
4. `GET /campaign/levels?campaign_id=1`
5. `GET /campaign/levels/1?campaign_id=1`
6. `POST /levels/1/start`
7. `GET /levels/1/game-state`
8. `POST /levels/1/answer`
9. `POST /levels/1/hint`
10. `POST /levels/1/end-game`

## Ports

Dans ton setup actuel :

```env
BDD_API_URL=http://127.0.0.1:5000
```

Ton back tourne sur :

```txt
http://127.0.0.1:5001
```

Donc dans Postman :

```txt
base_url = http://127.0.0.1:5001
```
