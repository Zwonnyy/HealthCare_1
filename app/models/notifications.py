from enum import StrEnum

from tortoise import fields, models


class NotificationType(StrEnum):
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    RECORD_CREATED = "RECORD_CREATED"
    GUIDE_COMPLETED = "GUIDE_COMPLETED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"


class Notification(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="notifications")
    notification_type = fields.CharEnumField(enum_type=NotificationType, max_length=30)
    title = fields.CharField(max_length=100)
    body = fields.TextField()
    is_read = fields.BooleanField(default=False)
    read_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"
