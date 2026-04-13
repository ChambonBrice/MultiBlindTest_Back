import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, "bdd")
DB_NAME = os.path.join(DB_PATH, "MBT.db")


class SettingsService:
    DEFAULT_SETTINGS = {
        "mainVolume": 100,
        "volumeMusic": 100,
        "volumeSFX": 100,
        "language": "FR",
    }

    @staticmethod
    def get_connection():
        os.makedirs(DB_PATH, exist_ok=True)
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def ensure_user_settings(conn, user_id):
        SettingsService.ensure_table(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Settings WHERE UserID = ?", (user_id,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(
                """
                INSERT INTO Settings (MainVolume, VolumeMusic, VolumeSFX, Language, UserID)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    SettingsService.DEFAULT_SETTINGS["mainVolume"],
                    SettingsService.DEFAULT_SETTINGS["volumeMusic"],
                    SettingsService.DEFAULT_SETTINGS["volumeSFX"],
                    SettingsService.DEFAULT_SETTINGS["language"],
                    user_id,
                ),
            )
            conn.commit()

    @staticmethod
    def serialize(row):
        if row is None:
            return None
        return {
            "mainVolume": row["MainVolume"],
            "volumeMusic": row["VolumeMusic"],
            "volumeSFX": row["VolumeSFX"],
            "language": row["Language"],
        }

    @staticmethod
    def get_settings(user_id):
        conn = SettingsService.get_connection()
        try:
            SettingsService.ensure_user_settings(conn, user_id)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT MainVolume, VolumeMusic, VolumeSFX, Language
                FROM Settings
                WHERE UserID = ?
                """,
                (user_id,),
            )
            return SettingsService.serialize(cursor.fetchone())
        finally:
            conn.close()

    @staticmethod
    def normalize_payload(data):
        if not data or not isinstance(data, dict):
            raise ValueError("JSON invalide")

        normalized = {}

        volume_fields = {
            "mainVolume": ["mainVolume", "MainVolume"],
            "volumeMusic": ["volumeMusic", "VolumeMusic"],
            "volumeSFX": ["volumeSFX", "VolumeSFX"],
        }

        for target_field, accepted_names in volume_fields.items():
            provided_value = None
            provided = False
            for field_name in accepted_names:
                if field_name in data:
                    provided_value = data[field_name]
                    provided = True
                    break

            if provided:
                try:
                    value = int(provided_value)
                except (TypeError, ValueError):
                    raise ValueError(f"{target_field} doit être un entier")

                if value < 0 or value > 100:
                    raise ValueError(f"{target_field} doit être compris entre 0 et 100")

                normalized[target_field] = value

        if "language" in data or "Language" in data:
            language = data.get("language", data.get("Language"))
            if not isinstance(language, str) or not language.strip():
                raise ValueError("language doit être une chaîne non vide")
            normalized["language"] = language.strip().upper()

        if not normalized:
            raise ValueError("Aucun paramètre valide à mettre à jour")

        return normalized

    @staticmethod
    def update_settings(user_id, data):
        normalized = SettingsService.normalize_payload(data)
        conn = SettingsService.get_connection()
        try:
            SettingsService.ensure_user_settings(conn, user_id)
            cursor = conn.cursor()

            set_clauses = []
            values = []
            mapping = {
                "mainVolume": "MainVolume",
                "volumeMusic": "VolumeMusic",
                "volumeSFX": "VolumeSFX",
                "language": "Language",
            }

            for key, value in normalized.items():
                set_clauses.append(f"{mapping[key]} = ?")
                values.append(value)

            values.append(user_id)
            cursor.execute(
                f"UPDATE Settings SET {', '.join(set_clauses)} WHERE UserID = ?",
                tuple(values),
            )
            conn.commit()

            cursor.execute(
                """
                SELECT MainVolume, VolumeMusic, VolumeSFX, Language
                FROM Settings
                WHERE UserID = ?
                """,
                (user_id,),
            )
            return SettingsService.serialize(cursor.fetchone())
        finally:
            conn.close()
