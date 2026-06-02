from enum import StrEnum

from tortoise import fields, models


class InteractionStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DrugInteraction(models.Model):
    id = fields.BigIntField(primary_key=True)
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="interactions")
    status = fields.CharEnumField(enum_type=InteractionStatus, default=InteractionStatus.PENDING)
    result_text = fields.TextField(null=True)
    has_warning = fields.BooleanField(default=False)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "drug_interactions"