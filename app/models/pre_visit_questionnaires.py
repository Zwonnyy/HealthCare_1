from tortoise import fields, models


class PreVisitQuestionnaire(models.Model):
    id = fields.BigIntField(primary_key=True)
    appointment = fields.ForeignKeyField("models.Appointment", related_name="pre_visit_questionnaires")
    patient = fields.ForeignKeyField("models.User", related_name="pre_visit_questionnaires")
    symptoms = fields.TextField()
    onset = fields.CharField(max_length=100, null=True)
    severity = fields.IntField(null=True)
    medications = fields.TextField(null=True)
    history = fields.TextField(null=True)
    questions = fields.TextField(null=True)
    ai_summary = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "pre_visit_questionnaires"
