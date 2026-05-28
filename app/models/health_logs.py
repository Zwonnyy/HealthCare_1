from enum import StrEnum

from tortoise import fields, models


class Mood(StrEnum):
    GREAT = "GREAT"
    GOOD = "GOOD"
    NORMAL = "NORMAL"
    BAD = "BAD"
    TERRIBLE = "TERRIBLE"


class AnalysisStatus(StrEnum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class HealthLog(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="health_logs")
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="health_logs", null=True)
    log_date = fields.DateField()
    pain_score = fields.IntField()  # 0~10
    mood = fields.CharEnumField(enum_type=Mood)
    symptoms_text = fields.TextField()
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "health_logs"


class HealthLogAnalysis(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="health_analyses")
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="health_analyses", null=True)
    analysis_text = fields.TextField(null=True)
    status = fields.CharEnumField(enum_type=AnalysisStatus, default=AnalysisStatus.PENDING)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "health_log_analyses"
