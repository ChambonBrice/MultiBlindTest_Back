import sqlite3
from datetime import datetime
from MultiBlindTest_Back.Library.Authentification import Authentification

class SubscriptionService:

    @staticmethod
    def get_user_subscription(user_id):
        conn = Authentification.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT Plan, Status, StartDate, EndDate, AutoRenew, Provider
            FROM Subscriptions
            WHERE UserID = ?
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "plan": row["Plan"],
            "status": row["Status"],
            "start_date": row["StartDate"],
            "end_date": row["EndDate"],
            "auto_renew": row["AutoRenew"],
            "provider": row["Provider"]
        }

    @staticmethod
    def has_active_subscription(user_id):
        subscription = SubscriptionService.get_user_subscription(user_id)

        if not subscription:
            return False

        if subscription["status"] != "active":
            return False

        if not subscription["end_date"]:
            return False

        try:
            end_date = datetime.fromisoformat(subscription["end_date"])
        except ValueError:
            return False

        return end_date > datetime.now()
