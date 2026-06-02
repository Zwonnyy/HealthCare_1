from enum import StrEnum

from tortoise import fields, models


class GoalType(StrEnum):
    WEIGHT = "WEIGHT"
    BLOOD_PRESSURE = "BLOOD_PRESSURE"
    EXERCISE_DAYS = "EXERCISE_DAYS"
    PAIN_SCORE = "PAIN_SCORE"
    CUSTOM = "CUSTOM"


class HealthGoal(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="health_goals")
    goal_type = fields.CharEnumField(enum_type=GoalType, max_length=20)
    title = fields.CharField(max_length=100)
    target_value = fields.FloatField()
    current_value = fields.FloatField(null=True)
    unit = fields.CharField(max_length=20)
    deadline = fields.DateField(null=True)
    achieved = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "health_goals"