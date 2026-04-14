from datetime import datetime

from MultiBlindTest_Back.Library.bdd_client import execute_sql


class SubscriptionService:

    @staticmethod
    def get_user_subscription(user_id):
        payload = execute_sql(
            """
            SELECT Plan, Status, StartDate, EndDate, AutoRenew, Provider
            FROM Subscriptions
            WHERE UserID = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        rows = payload.get("rows", [])
        if not rows:
            return None
        row = rows[0]
        return {
            "plan": row["Plan"],
            "status": row["Status"],
            "start_date": row["StartDate"],
            "end_date": row["EndDate"],
            "auto_renew": row["AutoRenew"],
            "provider": row["Provider"],
        }

    @staticmethod
    def has_active_subscription(user_id):
        subscription = SubscriptionService.get_user_subscription(user_id)
        if not subscription or subscription["status"] != "active" or not subscription["end_date"]:
            return False
        try:
            end_date = datetime.fromisoformat(subscription["end_date"])
        except ValueError:
            return False
        return end_date > datetime.now()
