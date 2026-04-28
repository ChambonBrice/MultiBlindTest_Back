from MultiBlindTest_Back.Library.bdd_client import execute_sql


class SettingsService:
    DEFAULT_SETTINGS = {
        'mainVolume': 100,
        'volumeMusic': 100,
        'volumeSFX': 100,
        'language': 'FR',
    }

    @staticmethod
    def ensure_user_settings(user_id):
        payload = execute_sql('SELECT 1 as ok FROM Settings WHERE UserID = ? LIMIT 1', (user_id,))
        if not payload.get('rows'):
            execute_sql(
                'INSERT INTO Settings (MainVolume, VolumeMusic, VolumeSFX, Language, UserID) VALUES (?, ?, ?, ?, ?)',
                (100, 100, 100, 'FR', user_id),
            )

    @staticmethod
    def serialize(row):
        if row is None:
            return None
        return {
            'mainVolume': row['MainVolume'],
            'volumeMusic': row['VolumeMusic'],
            'volumeSFX': row['VolumeSFX'],
            'language': row['Language'],
        }

    @staticmethod
    def get_settings(user_id):
        SettingsService.ensure_user_settings(user_id)
        payload = execute_sql('SELECT MainVolume, VolumeMusic, VolumeSFX, Language FROM Settings WHERE UserID = ?', (user_id,))
        rows = payload.get('rows', [])
        return SettingsService.serialize(rows[0] if rows else None)

    @staticmethod
    def normalize_payload(data):
        if not data or not isinstance(data, dict):
            raise ValueError('JSON invalide')
        normalized = {}
        volume_fields = {
            'mainVolume': ['mainVolume', 'MainVolume'],
            'volumeMusic': ['volumeMusic', 'VolumeMusic'],
            'volumeSFX': ['volumeSFX', 'VolumeSFX'],
        }
        for target_field, accepted_names in volume_fields.items():
            provided = next((data[n] for n in accepted_names if n in data), None)
            if provided is not None:
                try:
                    value = int(provided)
                except (TypeError, ValueError):
                    raise ValueError(f'{target_field} doit être un entier')
                if value < 0 or value > 100:
                    raise ValueError(f'{target_field} doit être compris entre 0 et 100')
                normalized[target_field] = value
        if 'language' in data or 'Language' in data:
            language = data.get('language', data.get('Language'))
            if not isinstance(language, str) or not language.strip():
                raise ValueError('language doit être une chaîne non vide')
            normalized['language'] = language.strip().upper()
        if not normalized:
            raise ValueError('Aucun paramètre valide à mettre à jour')
        return normalized

    @staticmethod
    def update_settings(user_id, data):
        normalized = SettingsService.normalize_payload(data)
        SettingsService.ensure_user_settings(user_id)
        set_clauses, values = [], []
        mapping = {'mainVolume': 'MainVolume', 'volumeMusic': 'VolumeMusic', 'volumeSFX': 'VolumeSFX', 'language': 'Language'}
        for key, value in normalized.items():
            set_clauses.append(f"{mapping[key]} = ?")
            values.append(value)
        values.append(user_id)
        execute_sql(f"UPDATE Settings SET {', '.join(set_clauses)} WHERE UserID = ?", tuple(values))
        return SettingsService.get_settings(user_id)
