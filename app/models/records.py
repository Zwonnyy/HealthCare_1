from tortoise import fields, models


class MedicalRecord(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="patient_records")
    doctor = fields.ForeignKeyField("models.User", related_name="doctor_records")
    diagnosis = fields.TextField()
    symptoms = fields.TextField()
    notes = fields.TextField(null=True)
    visited_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "medical_records"


class Prescription(models.Model):
    id = fields.BigIntField(primary_key=True)
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="prescriptions")
    medication_name = fields.CharField(max_length=100)
    dosage = fields.CharField(max_length=50)
    frequency = fields.CharField(max_length=50)
    duration_days = fields.IntField()
    instructions = fields.TextField(null=True)

    class Meta:
        table = "prescriptions"
