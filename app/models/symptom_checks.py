from enum import StrEnum

from tortoise import fields, models


class UrgencyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SymptomCheck(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="symptom_checks")
    symptom_text = fields.TextField()
    ai_assessment = fields.TextField(null=True)
    urgency = fields.CharEnumField(enum_type=UrgencyLevel, max_length=10, null=True)
    suggest_appointment = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "symptom_checks"
