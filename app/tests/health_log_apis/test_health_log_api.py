from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import hash_password
from app.main import app
from app.models.users import Gender, User, UserRole


class TestHealthLogAPI(TestCase):
    async def _create_patient(self, email: str) -> tuple[int, str]:
        signup_data = {
            "email": email,
            "password": "Password123!",
            "name": "테스트환자",
            "gender": "MALE",
            "birth_date": "1995-03-15",
            "phone_number": "01011112222",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        access_token = login_response.json()["access_token"]
        user = await User.get(email=email)
        return user.id, access_token

    async def _create_doctor(self, email: str) -> tuple[int, str]:
        doctor = await User.create(
            email=email,
            hashed_password=hash_password("Password123!"),
            name="테스트의사",
            gender=Gender.MALE,
            birthday="1980-01-01",
            phone_number="01033334444",
            role=UserRole.DOCTOR,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        return doctor.id, login_response.json()["access_token"]

    async def test_create_health_log_success(self):
        _, token = await self._create_patient("hl_create@example.com")
        payload = {
            "log_date": "2026-05-01",
            "pain_score": 3,
            "mood": "GOOD",
            "symptoms_text": "두통, 피로감",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/health-logs", json=payload, headers={"Authorization": f"Bearer {token}"}
            )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["pain_score"] == 3
        assert data["mood"] == "GOOD"
        assert data["symptoms_text"] == "두통, 피로감"

    async def test_create_health_log_requires_patient_role(self):
        _, doctor_token = await self._create_doctor("hl_doctor_create@example.com")
        payload = {
            "log_date": "2026-05-01",
            "pain_score": 2,
            "mood": "NORMAL",
            "symptoms_text": "테스트",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/health-logs", json=payload, headers={"Authorization": f"Bearer {doctor_token}"}
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_my_health_logs(self):
        _, token = await self._create_patient("hl_list@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "log_date": "2026-05-02",
            "pain_score": 5,
            "mood": "BAD",
            "symptoms_text": "관절통",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/health-logs", json=payload, headers=headers)
            response = await client.get("/api/v1/health-logs", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    async def test_get_health_log_by_id(self):
        _, token = await self._create_patient("hl_get@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "log_date": "2026-05-03",
            "pain_score": 7,
            "mood": "TERRIBLE",
            "symptoms_text": "심한 두통",
            "notes": "진통제 복용",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/health-logs", json=payload, headers=headers)
            log_id = create_response.json()["id"]
            response = await client.get(f"/api/v1/health-logs/{log_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["notes"] == "진통제 복용"

    async def test_get_health_log_other_patient_forbidden(self):
        _, token1 = await self._create_patient("hl_other1@example.com")
        _, token2 = await self._create_patient("hl_other2@example.com")
        payload = {
            "log_date": "2026-05-04",
            "pain_score": 4,
            "mood": "NORMAL",
            "symptoms_text": "약한 통증",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post(
                "/api/v1/health-logs", json=payload, headers={"Authorization": f"Bearer {token1}"}
            )
            log_id = create_response.json()["id"]
            response = await client.get(f"/api/v1/health-logs/{log_id}", headers={"Authorization": f"Bearer {token2}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_health_log_success(self):
        _, token = await self._create_patient("hl_delete@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "log_date": "2026-05-05",
            "pain_score": 1,
            "mood": "GREAT",
            "symptoms_text": "거의 회복",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/health-logs", json=payload, headers=headers)
            log_id = create_response.json()["id"]
            delete_response = await client.delete(f"/api/v1/health-logs/{log_id}", headers=headers)
            get_response = await client.get(f"/api/v1/health-logs/{log_id}", headers=headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_request_analysis_success(self):
        _, token = await self._create_patient("hl_analysis@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "log_date": "2026-05-06",
            "pain_score": 6,
            "mood": "BAD",
            "symptoms_text": "지속적인 두통",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/health-logs", json=payload, headers=headers)
            with patch("app.core.celery.celery_client.send_task") as mock_task:
                response = await client.post("/api/v1/health-logs/analyze", json={}, headers=headers)
                mock_task.assert_called_once_with("analyze_health_logs", args=[response.json()["id"]])
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()["status"] == "PENDING"

    async def test_get_analysis_result(self):
        _, token = await self._create_patient("hl_get_analysis@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "log_date": "2026-05-07",
            "pain_score": 5,
            "mood": "NORMAL",
            "symptoms_text": "보통 상태",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/health-logs", json=payload, headers=headers)
            with patch("app.core.celery.celery_client.send_task"):
                analysis_response = await client.post("/api/v1/health-logs/analyze", json={}, headers=headers)
            analysis_id = analysis_response.json()["id"]
            response = await client.get(f"/api/v1/health-logs/analyses/{analysis_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == analysis_id

    async def test_get_analysis_other_patient_forbidden(self):
        _, token1 = await self._create_patient("hl_ana_own@example.com")
        _, token2 = await self._create_patient("hl_ana_other@example.com")
        payload = {
            "log_date": "2026-05-08",
            "pain_score": 3,
            "mood": "GOOD",
            "symptoms_text": "양호",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/health-logs", json=payload, headers={"Authorization": f"Bearer {token1}"})
            with patch("app.core.celery.celery_client.send_task"):
                analysis_response = await client.post(
                    "/api/v1/health-logs/analyze", json={}, headers={"Authorization": f"Bearer {token1}"}
                )
            analysis_id = analysis_response.json()["id"]
            response = await client.get(
                f"/api/v1/health-logs/analyses/{analysis_id}",
                headers={"Authorization": f"Bearer {token2}"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN
