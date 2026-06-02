from enum import StrEnum

from tortoise import fields, models


class ReportStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class HealthReport(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="health_reports")
    year = fields.IntField()
    month = fields.IntField()
    report_text = fields.TextField(null=True)
    status = fields.CharEnumField(enum_type=ReportStatus, default=ReportStatus.PENDING, max_length=20)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "health_reports"
