from enum import StrEnum

from tortoise import fields, models


class AppointmentStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Appointment(models.Model):
    id = fields.BigIntField(primary_key=True)
    patient = fields.ForeignKeyField("models.User", related_name="patient_appointments")
    doctor = fields.ForeignKeyField("models.User", related_name="doctor_appointments")
    requested_at = fields.DatetimeField()
    status = fields.CharEnumField(enum_type=AppointmentStatus, default=AppointmentStatus.PENDING)
    patient_notes = fields.TextField(null=True)
    doctor_notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "appointments"
