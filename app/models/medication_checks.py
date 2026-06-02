from tortoise import fields, models


class MedicationCheck(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="medication_checks")
    prescription = fields.ForeignKeyField("models.Prescription", related_name="checks")
    check_date = fields.DateField()
    checked_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medication_checks"
        unique_together = (("prescription_id", "check_date"),)