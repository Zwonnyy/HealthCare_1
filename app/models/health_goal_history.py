from tortoise import fields, models


class HealthGoalHistory(models.Model):
    id = fields.BigIntField(primary_key=True)
    goal = fields.ForeignKeyField("models.HealthGoal", related_name="history")
    patient = fields.ForeignKeyField("models.User", related_name="goal_history")
    recorded_value = fields.FloatField()
    recorded_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "health_goal_history"
