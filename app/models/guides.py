from enum import StrEnum

from tortoise import fields, models


class GuideStatus(StrEnum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Guide(models.Model):
    id = fields.BigIntField(primary_key=True)
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="guides")
    medication_guide = fields.TextField(null=True)
    lifestyle_guide = fields.TextField(null=True)
    status = fields.CharEnumField(enum_type=GuideStatus, default=GuideStatus.PENDING)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "guides"