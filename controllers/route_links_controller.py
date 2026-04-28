from flask import Blueprint, jsonify

route_links_bp = Blueprint("route_links", __name__, url_prefix="/routes")

ROUTE_LINKS = [
    {
        "feature": "Auth - inscription",
        "front_back_route": "POST /register ou POST /mbt/register",
        "bdd_route": "POST /mbt/register",
        "bdd_tables": ["Users", "Settings", "Profils", "Rank", "Subscriptions"],
        "auth_required": False,
        "body_example": {"name": "testuser", "nom": "Test", "email": "test@example.com", "password": "Password123", "age": 18},
    },
    {
        "feature": "Auth - connexion joueur",
        "front_back_route": "POST /mbt/login ou POST /login/user",
        "bdd_route": "POST /mbt/login",
        "bdd_tables": ["Users"],
        "auth_required": False,
        "body_example": {"name": "testuser", "password": "Password123"},
    },
    {
        "feature": "Campagne - liste niveaux + progression joueur",
        "front_back_route": "GET /campaign/levels?campaign_id=1",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["Campaign", "CampaignLevels", "Levels", "Levels_Etat", "Victory"],
        "auth_required": True,
        "body_example": None,
    },
    {
        "feature": "Campagne - detail niveau",
        "front_back_route": "GET /campaign/levels/<level_id>?campaign_id=1",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["Levels", "Levels_Etat", "Music", "Victory"],
        "auth_required": True,
        "body_example": None,
    },
    {
        "feature": "Campagne - terminer niveau et debloquer suivant",
        "front_back_route": "POST /campaign/levels/<level_id>/complete",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["Levels_Etat", "CampaignLevels"],
        "auth_required": True,
        "body_example": {"campaign_id": 1},
    },
    {
        "feature": "Level Creator - creer niveau custom",
        "front_back_route": "POST /creator/levels",
        "bdd_route": "POST /mbt/sql/script puis POST /mbt/sql/execute",
        "bdd_tables": ["LevelsCustom"],
        "auth_required": True,
        "body_example": {"title": "Mon Blind Test", "artist_tag": "Pop", "theme": "NEON_PINK"},
    },
    {
        "feature": "Level Creator - lister mes niveaux",
        "front_back_route": "GET /creator/levels",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["LevelsCustom"],
        "auth_required": True,
        "body_example": None,
    },
    {
        "feature": "Level Creator - detail niveau custom",
        "front_back_route": "GET /creator/levels/<level_id>",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["LevelsCustom", "LevelTracks"],
        "auth_required": True,
        "body_example": None,
    },
    {
        "feature": "Level Creator - ajouter lien YouTube / clip config",
        "front_back_route": "POST /creator/levels/<level_id>/tracks",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["LevelTracks"],
        "auth_required": True,
        "body_example": {"youtube_url": "https://youtube.com/watch?v=...", "start_point": 30, "duration": 12, "difficulty": 1},
    },
    {
        "feature": "Jeu - demarrer partie",
        "front_back_route": "POST /levels/<level_id>/start",
        "bdd_route": "POST /mbt/sql/script puis POST /mbt/sql/execute",
        "bdd_tables": ["GameSessions", "GameSessionFoundTracks", "Levels", "Levels_Etat", "Music"],
        "auth_required": True,
        "body_example": {"campaign_id": 1},
    },
    {
        "feature": "Jeu - etat partie",
        "front_back_route": "GET /levels/<level_id>/game-state",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["GameSessions", "GameSessionFoundTracks", "Levels", "Music"],
        "auth_required": True,
        "body_example": None,
    },
    {
        "feature": "Jeu - envoyer reponse",
        "front_back_route": "POST /levels/<level_id>/answer",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["GameSessions", "GameSessionFoundTracks", "Music"],
        "auth_required": True,
        "body_example": {"guess": "Titre musique", "time_left": 42},
    },
    {
        "feature": "Jeu - demander indice",
        "front_back_route": "POST /levels/<level_id>/hint",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["GameSessions", "Levels"],
        "auth_required": True,
        "body_example": {},
    },
    {
        "feature": "Jeu - fin de partie/resultats",
        "front_back_route": "POST /levels/<level_id>/end-game",
        "bdd_route": "POST /mbt/sql/execute",
        "bdd_tables": ["GameSessions", "Victory", "Profils", "Levels_Etat", "CampaignLevels"],
        "auth_required": True,
        "body_example": {"campaign_id": 1, "time_left": 20},
    },
    {
        "feature": "Musiques legacy niveau",
        "front_back_route": "GET /mbt/music/<level_id>",
        "bdd_route": "GET /mbt/music/<level_id>",
        "bdd_tables": ["Music"],
        "auth_required": False,
        "body_example": None,
    },
    {
        "feature": "Community/anciens niveaux publics",
        "front_back_route": "GET /mbt/levels, GET /mbt/levels/<public_id>",
        "bdd_route": "GET /mbt/levels, GET /mbt/levels/<public_id>",
        "bdd_tables": ["Levels", "Community_Level", "Music"],
        "auth_required": False,
        "body_example": None,
    },
]


@route_links_bp.route("/links", methods=["GET"])
def get_route_links():
    return jsonify({"count": len(ROUTE_LINKS), "routes": ROUTE_LINKS}), 200


@route_links_bp.route("/health", methods=["GET"])
def route_links_health():
    return jsonify({"status": "ok", "message": "Mapping Back <-> BDD disponible sur GET /routes/links"}), 200
