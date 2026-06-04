from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import hash_password
from app.main import app
from app.models.users import Gender, User, UserRole


class TestReminderAPI(TestCase):
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

    async def test_create_reminder_success(self):
        """복약 알림 생성"""
        _, token = await self._create_patient("rem_create@example.com", "01099990041")
        payload = {"name": "혈압약", "reminder_time": "08:00"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/reminders", json=payload, headers={"Authorization": f"Bearer {token}"}
            )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "혈압약"
        assert data["reminder_time"] == "08:00"
        assert data["enabled"] is True

    async def test_list_reminders_empty(self):
        """알림 없을 때 빈 목록"""
        _, token = await self._create_patient("rem_empty@example.com", "01099990042")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/reminders", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_list_reminders_after_create(self):
        """알림 생성 후 목록에 1건"""
        _, token = await self._create_patient("rem_list@example.com", "01099990043")
        headers = {"Authorization": f"Bearer {token}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/reminders", json={"name": "비타민", "reminder_time": "09:00"}, headers=headers)
            response = await client.get("/api/v1/reminders", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    async def test_update_reminder_enabled(self):
        """알림 비활성화"""
        _, token = await self._create_patient("rem_disable@example.com", "01099990044")
        headers = {"Authorization": f"Bearer {token}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/reminders", json={"name": "혈당약", "reminder_time": "12:00"}, headers=headers
            )
            rem_id = create_resp.json()["id"]
            response = await client.patch(f"/api/v1/reminders/{rem_id}", json={"enabled": False}, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["enabled"] is False

    async def test_update_reminder_time(self):
        """알림 시각 변경"""
        _, token = await self._create_patient("rem_time@example.com", "01099990045")
        headers = {"Authorization": f"Bearer {token}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/reminders", json={"name": "수면제", "reminder_time": "21:00"}, headers=headers
            )
            rem_id = create_resp.json()["id"]
            response = await client.patch(
                f"/api/v1/reminders/{rem_id}", json={"reminder_time": "22:30"}, headers=headers
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["reminder_time"] == "22:30"

    async def test_delete_reminder(self):
        """알림 삭제 후 목록에서 사라짐"""
        _, token = await self._create_patient("rem_delete@example.com", "01099990046")
        headers = {"Authorization": f"Bearer {token}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/reminders", json={"name": "소화제", "reminder_time": "13:00"}, headers=headers
            )
            rem_id = create_resp.json()["id"]
            delete_resp = await client.delete(f"/api/v1/reminders/{rem_id}", headers=headers)
            list_resp = await client.get("/api/v1/reminders", headers=headers)
        assert delete_resp.status_code == status.HTTP_204_NO_CONTENT
        assert list_resp.json() == []

    async def test_reminder_requires_patient_role(self):
        """의사 토큰으로 알림 생성 시 403"""
        _, doctor_token = await self._create_doctor("rem_doc@example.com", "01099990047")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/reminders",
                json={"name": "약", "reminder_time": "08:00"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN
