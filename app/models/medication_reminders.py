from tortoise import fields, models


class MedicationReminder(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="medication_reminders")
    name = fields.CharField(max_length=100)           # 복약명 (예: 암로디핀 5mg)
    reminder_time = fields.CharField(max_length=5)   # HH:MM 형식
    enabled = fields.BooleanField(default=True)
    last_notified_date = fields.DateField(null=True)  # 마지막 알림 발송 날짜
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medication_reminders"