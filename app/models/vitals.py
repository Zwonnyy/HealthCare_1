from tortoise import fields, models


class VitalRecord(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="vital_records")
    systolic = fields.IntField(null=True)  # 수축기 혈압
    diastolic = fields.IntField(null=True)  # 이완기 혈압
    blood_sugar = fields.FloatField(null=True)  # 혈당 mg/dL
    weight = fields.FloatField(null=True)  # 체중 kg
    heart_rate = fields.IntField(null=True)  # 심박수 bpm
    notes = fields.TextField(null=True)
    alert_message = fields.TextField(null=True)  # Gemini 이상 감지 메시지
    recorded_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "vital_records"
