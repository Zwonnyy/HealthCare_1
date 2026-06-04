from unittest.mock import AsyncMock, Mock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import hash_password
from app.main import app
from app.models.users import Gender, User, UserRole


def _make_genai_mock(urgency: str = "LOW", suggest: bool = False) -> Mock:
    mock_resp = Mock()
    mock_resp.text = (
        f'{{"urgency": "{urgency}", "assessment": "AI 평가 내용입니다.", '
        f'"recommendation": "충분히 쉬세요.", "suggest_appointment": {"true" if suggest else "false"}}}'
    )
    mock_instance = AsyncMock()
    mock_instance.aio.models.generate_content = AsyncMock(return_value=mock_resp)
    return Mock(return_value=mock_instance)


class TestSymptomCheckAPI(TestCase):
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

    async def test_check_symptoms_success(self):
        """증상 체크 성공 — LOW 긴급도"""
        _, token = await self._create_patient("sc_low@example.com", "01099990011")
        with (
            patch("app.services.symptom_checks.search_guidelines", new=AsyncMock(return_value="")),
            patch("app.services.symptom_checks.genai.Client", new=_make_genai_mock("LOW", False)),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/symptom-check",
                    json={"symptom_text": "두통이 있어요"},
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["urgency"] == "LOW"
        assert data["suggest_appointment"] is False
        assert data["symptom_text"] == "두통이 있어요"

    async def test_check_symptoms_high_urgency(self):
        """HIGH 긴급도 — 진료 예약 권고"""
        _, token = await self._create_patient("sc_high@example.com", "01099990012")
        with (
            patch("app.services.symptom_checks.search_guidelines", new=AsyncMock(return_value="")),
            patch("app.services.symptom_checks.genai.Client", new=_make_genai_mock("HIGH", True)),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/symptom-check",
                    json={"symptom_text": "가슴이 너무 아파요"},
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["urgency"] == "HIGH"
        assert data["suggest_appointment"] is True

    async def test_list_symptom_checks_empty(self):
        """기록 없을 때 빈 목록"""
        _, token = await self._create_patient("sc_empty@example.com", "01099990013")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/symptom-check", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_list_symptom_checks_after_check(self):
        """1건 체크 후 목록에 1건"""
        _, token = await self._create_patient("sc_list@example.com", "01099990014")
        headers = {"Authorization": f"Bearer {token}"}
        with (
            patch("app.services.symptom_checks.search_guidelines", new=AsyncMock(return_value="")),
            patch("app.services.symptom_checks.genai.Client", new=_make_genai_mock()),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/api/v1/symptom-check", json={"symptom_text": "기침이 나요"}, headers=headers)
                response = await client.get("/api/v1/symptom-check", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    async def test_symptom_check_requires_patient_role(self):
        """의사 토큰으로 증상 체크 시 403"""
        _, doctor_token = await self._create_doctor("sc_doc@example.com", "01099990015")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/symptom-check",
                json={"symptom_text": "두통"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN
