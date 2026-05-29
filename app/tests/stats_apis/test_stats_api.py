from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import hash_password
from app.main import app
from app.models.users import Gender, User, UserRole


class TestStatsAPI(TestCase):
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

    # ── 환자 통계 ────────────────────────────────────────────────

    async def test_patient_stats_no_data(self):
        """건강 일지·진료기록·메시지가 없는 초기 상태 검증"""
        _, token = await self._create_patient("stat_empty@example.com", "01011110101")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/stats/patient", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_records"] == 0
        assert data["unread_messages"] == 0
        assert data["health_log_stats"]["total"] == 0
        assert data["health_log_stats"]["avg_pain_score_7d"] is None
        assert data["health_log_stats"]["avg_pain_score_30d"] is None
        assert data["health_log_stats"]["pain_trend_14d"] == []
        dist = data["mood_distribution_30d"]
        assert all(dist[mood] == 0 for mood in ["GREAT", "GOOD", "NORMAL", "BAD", "TERRIBLE"])

    async def test_patient_stats_with_health_logs(self):
        """건강 일지 작성 후 통계 집계 검증"""
        _, token = await self._create_patient("stat_logs@example.com", "01011110102")
        headers = {"Authorization": f"Bearer {token}"}
        logs = [
            {"log_date": "2026-05-27", "pain_score": 4, "mood": "BAD", "symptoms_text": "두통"},
            {"log_date": "2026-05-28", "pain_score": 6, "mood": "TERRIBLE", "symptoms_text": "심한 두통"},
            {"log_date": "2026-05-29", "pain_score": 2, "mood": "GOOD", "symptoms_text": "호전"},
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for log in logs:
                await client.post("/api/v1/health-logs", json=log, headers=headers)
            response = await client.get("/api/v1/stats/patient", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        stats = data["health_log_stats"]
        assert stats["total"] == 3
        assert stats["avg_pain_score_7d"] == round((4 + 6 + 2) / 3, 1)
        assert stats["avg_pain_score_30d"] == round((4 + 6 + 2) / 3, 1)
        assert len(stats["pain_trend_14d"]) == 3

        dist = data["mood_distribution_30d"]
        assert dist["BAD"] == 1
        assert dist["TERRIBLE"] == 1
        assert dist["GOOD"] == 1
        assert dist["GREAT"] == 0

    async def test_patient_stats_unread_messages(self):
        """미열람 메시지 수 집계 검증"""
        _, doctor_token = await self._create_doctor("stat_doc_msg@example.com", "01033330101")
        patient_id, patient_token = await self._create_patient("stat_pat_msg@example.com", "01011110103")
        headers_d = {"Authorization": f"Bearer {doctor_token}"}
        headers_p = {"Authorization": f"Bearer {patient_token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 의사가 환자에게 메시지 2건 전송
            for content in ["메시지1", "메시지2"]:
                await client.post(
                    "/api/v1/messages",
                    json={"receiver_id": patient_id, "content": content},
                    headers=headers_d,
                )
            response = await client.get("/api/v1/stats/patient", headers=headers_p)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["unread_messages"] == 2

    async def test_patient_stats_total_records(self):
        """진료기록 수 집계 검증"""
        doctor_id, doctor_token = await self._create_doctor("stat_doc_rec@example.com", "01033330102")
        patient_id, patient_token = await self._create_patient("stat_pat_rec@example.com", "01011110104")
        headers_d = {"Authorization": f"Bearer {doctor_token}"}

        record_data = {
            "patient_id": patient_id,
            "diagnosis": "감기",
            "symptoms": "기침, 콧물",
            "visited_at": "2026-05-20T10:00:00",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/records", json=record_data, headers=headers_d)
            await client.post(
                "/api/v1/records", json={**record_data, "visited_at": "2026-05-21T10:00:00"}, headers=headers_d
            )
            response = await client.get("/api/v1/stats/patient", headers={"Authorization": f"Bearer {patient_token}"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total_records"] == 2

    async def test_patient_stats_requires_patient_role(self):
        """의사 토큰으로 환자 통계 조회 시 403"""
        _, doctor_token = await self._create_doctor("stat_doc_forbidden@example.com", "01033330103")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/stats/patient", headers={"Authorization": f"Bearer {doctor_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ── 의사 통계 ────────────────────────────────────────────────

    async def test_doctor_stats_no_data(self):
        """진료기록이 없는 의사의 초기 상태 검증"""
        _, token = await self._create_doctor("stat_doc_empty@example.com", "01033330104")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/stats/doctor", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_patients"] == 0
        assert data["total_records"] == 0
        assert data["records_last_30d"] == 0
        assert data["unread_messages"] == 0
        assert data["pending_guides"] == 0

    async def test_doctor_stats_with_records(self):
        """진료기록 작성 후 의사 통계 집계 검증"""
        doctor_id, doctor_token = await self._create_doctor("stat_doc_data@example.com", "01033330105")
        patient1_id, _ = await self._create_patient("stat_pat_d1@example.com", "01011110105")
        patient2_id, _ = await self._create_patient("stat_pat_d2@example.com", "01011110106")
        headers_d = {"Authorization": f"Bearer {doctor_token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 환자1에게 2건, 환자2에게 1건 → 환자 2명, 기록 3건
            for patient_id in [patient1_id, patient1_id, patient2_id]:
                await client.post(
                    "/api/v1/records",
                    json={
                        "patient_id": patient_id,
                        "diagnosis": "테스트진단",
                        "symptoms": "테스트증상",
                        "visited_at": "2026-05-28T10:00:00",
                    },
                    headers=headers_d,
                )
            response = await client.get("/api/v1/stats/doctor", headers=headers_d)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_patients"] == 2
        assert data["total_records"] == 3
        assert data["records_last_30d"] == 3

    async def test_doctor_stats_unread_messages(self):
        """의사의 미열람 메시지 수 집계 검증"""
        doctor_id, doctor_token = await self._create_doctor("stat_doc_unread@example.com", "01033330106")
        _, patient_token = await self._create_patient("stat_pat_unread@example.com", "01011110107")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 환자가 의사에게 메시지 3건 전송
            for content in ["질문1", "질문2", "질문3"]:
                await client.post(
                    "/api/v1/messages",
                    json={"receiver_id": doctor_id, "content": content},
                    headers={"Authorization": f"Bearer {patient_token}"},
                )
            response = await client.get("/api/v1/stats/doctor", headers={"Authorization": f"Bearer {doctor_token}"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["unread_messages"] == 3

    async def test_doctor_stats_requires_doctor_role(self):
        """환자 토큰으로 의사 통계 조회 시 403"""
        _, patient_token = await self._create_patient("stat_pat_forbidden@example.com", "01011110108")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/stats/doctor", headers={"Authorization": f"Bearer {patient_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
