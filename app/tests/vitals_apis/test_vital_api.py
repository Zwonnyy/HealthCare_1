from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import hash_password
from app.main import app
from app.models.users import Gender, User, UserRole


class TestVitalAPI(TestCase):
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

    async def test_record_vital_success(self):
        """정상 범위 바이탈 기록 — alert_message 없음"""
        _, token = await self._create_patient("vital_ok@example.com", "01099990001")
        payload = {"systolic": 120, "diastolic": 80, "heart_rate": 72}
        with patch("app.services.vitals._check_alert", new=AsyncMock(return_value=None)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/vitals", json=payload, headers={"Authorization": f"Bearer {token}"}
                )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["systolic"] == 120
        assert data["diastolic"] == 80
        assert data["alert_message"] is None

    async def test_record_vital_with_alert(self):
        """이상 수치 — alert_message 반환"""
        _, token = await self._create_patient("vital_alert@example.com", "01099990002")
        payload = {"systolic": 180, "diastolic": 110}
        alert_msg = "혈압이 매우 높습니다. 즉시 진료를 받으세요."
        with patch("app.services.vitals._check_alert", new=AsyncMock(return_value=alert_msg)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/vitals", json=payload, headers={"Authorization": f"Bearer {token}"}
                )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["alert_message"] == alert_msg

    async def test_list_vitals_empty(self):
        """기록 없을 때 빈 목록"""
        _, token = await self._create_patient("vital_empty@example.com", "01099990003")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/vitals", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_list_vitals_after_record(self):
        """기록 후 목록에 1건 존재"""
        _, token = await self._create_patient("vital_list@example.com", "01099990004")
        headers = {"Authorization": f"Bearer {token}"}
        with patch("app.services.vitals._check_alert", new=AsyncMock(return_value=None)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/api/v1/vitals", json={"weight": 68.5}, headers=headers)
                response = await client.get("/api/v1/vitals", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        assert response.json()[0]["weight"] == 68.5

    async def test_vital_requires_patient_role(self):
        """의사 토큰으로 바이탈 기록 시 403"""
        _, doctor_token = await self._create_doctor("vital_doc@example.com", "01099990005")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/vitals",
                json={"systolic": 120, "diastolic": 80},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN
