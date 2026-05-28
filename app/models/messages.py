from tortoise import fields, models


class Message(models.Model):
    id = fields.BigIntField(primary_key=True)
    sender = fields.ForeignKeyField("models.User", related_name="sent_messages")
    receiver = fields.ForeignKeyField("models.User", related_name="received_messages")
    record = fields.ForeignKeyField("models.MedicalRecord", related_name="messages", null=True)
    content = fields.TextField()
    is_read = fields.BooleanField(default=False)
    read_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "messages"
