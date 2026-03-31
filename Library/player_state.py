class PlayerState:
    @staticmethod
    def create_player_round_state(db, round_id, user_id):
        db.execute("""
            INSERT INTO PlayerRoundState (
                round_id, user_id, found_count, time_left_ms, round_score, status
            )
            VALUES (?, ?, 0, NULL, 0, 'playing')
        """, (round_id, user_id))

    @staticmethod
    def get_player_round_state(db, round_id, user_id):
        db.execute("""
            SELECT *
            FROM PlayerRoundState
            WHERE round_id = ? AND user_id = ?
        """, (round_id, user_id))
        return db.fetchone()

    @staticmethod
    def mark_track_found(db, round_id, user_id, round_track_id, points_awarded):
        db.execute("""
            INSERT INTO PlayerRoundFoundTracks (
                round_id, user_id, round_track_id, points_awarded
            )
            VALUES (?, ?, ?, ?)
        """, (round_id, user_id, round_track_id, points_awarded))

        db.execute("""
            UPDATE PlayerRoundState
            SET found_count = found_count + 1,
                round_score = round_score + ?
            WHERE round_id = ? AND user_id = ?
        """, (points_awarded, round_id, user_id))

    @staticmethod
    def has_player_found_track(db, round_id, user_id, round_track_id):
        db.execute("""
            SELECT 1
            FROM PlayerRoundFoundTracks
            WHERE round_id = ? AND user_id = ? AND round_track_id = ?
        """, (round_id, user_id, round_track_id))
        return db.fetchone() is not None

    @staticmethod
    def get_found_tracks(db, round_id, user_id):
        db.execute("""
            SELECT round_track_id, found_at, points_awarded
            FROM PlayerRoundFoundTracks
            WHERE round_id = ? AND user_id = ?
            ORDER BY found_at ASC
        """, (round_id, user_id))
        return db.fetchall()

    @staticmethod
    def finish_player_round(db, round_id, user_id, time_left_ms):
        db.execute("""
            UPDATE PlayerRoundState
            SET status = 'finished',
                completed_at = CURRENT_TIMESTAMP,
                time_left_ms = ?
            WHERE round_id = ? AND user_id = ?
        """, (time_left_ms, round_id, user_id))

    @staticmethod
    def timeout_player_round(db, round_id, user_id):
        db.execute("""
            UPDATE PlayerRoundState
            SET status = 'timeout'
            WHERE round_id = ? AND user_id = ? AND status = 'playing'
        """, (round_id, user_id))

    @staticmethod
    def get_round_leaderboard(db, round_id):
        db.execute("""
            SELECT
                prs.user_id,
                u.name,
                prs.found_count,
                prs.round_score,
                prs.time_left_ms,
                prs.status,
                prs.completed_at
            FROM PlayerRoundState prs
            JOIN Users u ON u.id = prs.user_id
            WHERE prs.round_id = ?
            ORDER BY prs.round_score DESC,
                     prs.found_count DESC,
                     prs.time_left_ms DESC,
                     prs.completed_at ASC
        """, (round_id,))
        return db.fetchall()

    @staticmethod
    def are_all_players_done(db, round_id):
        db.execute("""
            SELECT COUNT(*) AS remaining
            FROM PlayerRoundState
            WHERE round_id = ? AND status = 'playing'
        """, (round_id,))
        row = db.fetchone()
        return row["remaining"] == 0