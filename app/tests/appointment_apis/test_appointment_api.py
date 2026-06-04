from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import hash_password
from app.main import app
from app.models.users import Gender, User, UserRole

REQUESTED_AT = "2027-01-15T10:00:00"


class TestAppointmentAPI(TestCase):
    async def _create_patient(self, email: str, phone: str) -> tuple[int, str]:
        signup_data = {
            "email": email,
            "password": "Password123!",
            "name": "테스트환자",
            "gender": "FEMALE",
            "birth_date": "1995-06-20",
            "phone_number": phone,
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        user = await User.get(email=email)
        return user.id, login_resp.json()["access_token"]

    async def _create_doctor(self, email: str, phone: str) -> tuple[int, str]:
        doctor = await User.create(
            email=email,
            hashed_password=hash_password("Password123!"),
            name="테스트의사",
            gender=Gender.MALE,
            birthday="1978-03-10",
            phone_number=phone,
            role=UserRole.DOCTOR,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        return doctor.id, login_resp.json()["access_token"]

    async def test_create_appointment_success(self):
        """환자가 예약 생성 — PENDING 상태"""
        doctor_id, _ = await self._create_doctor("appt_doc1@example.com", "01099990021")
        _, patient_token = await self._create_patient("appt_pat1@example.com", "01099990022")
        payload = {"doctor_id": doctor_id, "requested_at": REQUESTED_AT, "patient_notes": "진료 부탁드려요"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/appointments", json=payload, headers={"Authorization": f"Bearer {patient_token}"}
            )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["doctor_id"] == doctor_id
        assert data["patient_notes"] == "진료 부탁드려요"

    async def test_get_appointments_as_patient(self):
        """환자로 예약 목록 조회"""
        doctor_id, _ = await self._create_doctor("appt_doc2@example.com", "01099990023")
        _, patient_token = await self._create_patient("appt_pat2@example.com", "01099990024")
        headers = {"Authorization": f"Bearer {patient_token}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/appointments", json={"doctor_id": doctor_id, "requested_at": REQUESTED_AT}, headers=headers
            )
            response = await client.get("/api/v1/appointments", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1

    async def test_get_appointments_as_doctor(self):
        """의사로 예약 목록 조회"""
        doctor_id, doctor_token = await self._create_doctor("appt_doc3@example.com", "01099990025")
        _, patient_token = await self._create_patient("appt_pat3@example.com", "01099990026")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/appointments",
                json={"doctor_id": doctor_id, "requested_at": REQUESTED_AT},
                headers={"Authorization": f"Bearer {patient_token}"},
            )
            response = await client.get("/api/v1/appointments", headers={"Authorization": f"Bearer {doctor_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1

    async def test_doctor_can_confirm_appointment(self):
        """의사가 예약 CONFIRMED로 변경"""
        doctor_id, doctor_token = await self._create_doctor("appt_doc4@example.com", "01099990027")
        _, patient_token = await self._create_patient("appt_pat4@example.com", "01099990028")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/appointments",
                json={"doctor_id": doctor_id, "requested_at": REQUESTED_AT},
                headers={"Authorization": f"Bearer {patient_token}"},
            )
            appt_id = create_resp.json()["id"]
            response = await client.patch(
                f"/api/v1/appointments/{appt_id}",
                json={"status": "CONFIRMED", "doctor_notes": "확정됐습니다."},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "CONFIRMED"

    async def test_doctor_cannot_access_other_doctor_appointment(self):
        """다른 의사는 예약 상태 변경 불가 — 403"""
        doctor_id, _ = await self._create_doctor("appt_doc5@example.com", "01099990029")
        _, other_doctor_token = await self._create_doctor("appt_doc6@example.com", "01099990030")
        _, patient_token = await self._create_patient("appt_pat5@example.com", "01099990031")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/appointments",
                json={"doctor_id": doctor_id, "requested_at": REQUESTED_AT},
                headers={"Authorization": f"Bearer {patient_token}"},
            )
            appt_id = create_resp.json()["id"]
            response = await client.patch(
                f"/api/v1/appointments/{appt_id}",
                json={"status": "CONFIRMED"},
                headers={"Authorization": f"Bearer {other_doctor_token}"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_patient_can_cancel_appointment(self):
        """환자가 예약 취소 — 204"""
        doctor_id, _ = await self._create_doctor("appt_doc7@example.com", "01099990032")
        _, patient_token = await self._create_patient("appt_pat6@example.com", "01099990033")
        headers = {"Authorization": f"Bearer {patient_token}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/appointments",
                json={"doctor_id": doctor_id, "requested_at": REQUESTED_AT},
                headers=headers,
            )
            appt_id = create_resp.json()["id"]
            response = await client.delete(f"/api/v1/appointments/{appt_id}", headers=headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_patient_cannot_cancel_other_patient_appointment(self):
        """다른 환자의 예약 취소 불가 — 403"""
        doctor_id, _ = await self._create_doctor("appt_doc8@example.com", "01099990034")
        _, patient1_token = await self._create_patient("appt_pat7@example.com", "01099990035")
        _, patient2_token = await self._create_patient("appt_pat8@example.com", "01099990036")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/appointments",
                json={"doctor_id": doctor_id, "requested_at": REQUESTED_AT},
                headers={"Authorization": f"Bearer {patient1_token}"},
            )
            appt_id = create_resp.json()["id"]
            response = await client.delete(
                f"/api/v1/appointments/{appt_id}",
                headers={"Authorization": f"Bearer {patient2_token}"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_appointment_requires_patient_role(self):
        """의사 토큰으로 예약 생성 시 403"""
        doctor_id, doctor_token = await self._create_doctor("appt_doc9@example.com", "01099990037")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/appointments",
                json={"doctor_id": doctor_id, "requested_at": REQUESTED_AT},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN
