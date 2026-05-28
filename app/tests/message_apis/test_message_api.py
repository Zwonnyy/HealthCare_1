from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import hash_password
from app.main import app
from app.models.users import Gender, User, UserRole


class TestMessageAPI(TestCase):
    async def _create_patient(self, email: str, phone: str = "01011112222") -> tuple[int, str]:
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
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        user = await User.get(email=email)
        return user.id, login_response.json()["access_token"]

    async def _create_doctor(self, email: str, phone: str = "01033334444") -> tuple[int, str]:
        doctor = await User.create(
            email=email,
            hashed_password=hash_password("Password123!"),
            name="테스트의사",
            gender=Gender.MALE,
            birthday="1978-04-10",
            phone_number=phone,
            role=UserRole.DOCTOR,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        return doctor.id, login_response.json()["access_token"]

    async def test_send_message_doctor_to_patient(self):
        doctor_id, doctor_token = await self._create_doctor("msg_doc1@example.com", "01011110001")
        patient_id, _ = await self._create_patient("msg_pat1@example.com", "01022220001")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/messages",
                json={"receiver_id": patient_id, "content": "안녕하세요 환자분."},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["sender_id"] == doctor_id
        assert data["receiver_id"] == patient_id
        assert data["is_read"] is False

    async def test_send_message_patient_to_doctor(self):
        doctor_id, _ = await self._create_doctor("msg_doc2@example.com", "01011110002")
        patient_id, patient_token = await self._create_patient("msg_pat2@example.com", "01022220002")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/messages",
                json={"receiver_id": doctor_id, "content": "선생님 질문이 있어요."},
                headers={"Authorization": f"Bearer {patient_token}"},
            )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["sender_id"] == patient_id

    async def test_send_message_to_same_role_fails(self):
        _, doctor_token = await self._create_doctor("msg_doc3@example.com", "01011110003")
        other_doctor_id, _ = await self._create_doctor("msg_doc4@example.com", "01011110004")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/messages",
                json={"receiver_id": other_doctor_id, "content": "같은 의사에게 보내기"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_send_message_to_self_fails(self):
        doctor_id, doctor_token = await self._create_doctor("msg_doc5@example.com", "01011110005")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/messages",
                json={"receiver_id": doctor_id, "content": "자기 자신에게"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_inbox(self):
        _, doctor_token = await self._create_doctor("msg_doc6@example.com", "01011110006")
        patient_id, patient_token = await self._create_patient("msg_pat6@example.com", "01022220006")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 의사가 환자에게 메시지 전송
            await client.post(
                "/api/v1/messages",
                json={"receiver_id": patient_id, "content": "받은 메시지 테스트"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
            # 환자의 수신함 조회
            response = await client.get("/api/v1/messages/inbox", headers={"Authorization": f"Bearer {patient_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        assert response.json()[0]["content"] == "받은 메시지 테스트"

    async def test_get_sent(self):
        doctor_id, doctor_token = await self._create_doctor("msg_doc7@example.com", "01011110007")
        patient_id, _ = await self._create_patient("msg_pat7@example.com", "01022220007")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/messages",
                json={"receiver_id": patient_id, "content": "보낸 메시지 테스트"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
            response = await client.get("/api/v1/messages/sent", headers={"Authorization": f"Bearer {doctor_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    async def test_get_unread_count(self):
        _, doctor_token = await self._create_doctor("msg_doc8@example.com", "01011110008")
        patient_id, patient_token = await self._create_patient("msg_pat8@example.com", "01022220008")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/messages",
                json={"receiver_id": patient_id, "content": "읽지 않은 메시지"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
            response = await client.get(
                "/api/v1/messages/unread-count", headers={"Authorization": f"Bearer {patient_token}"}
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1

    async def test_get_message_marks_as_read(self):
        _, doctor_token = await self._create_doctor("msg_doc9@example.com", "01011110009")
        patient_id, patient_token = await self._create_patient("msg_pat9@example.com", "01022220009")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            send_response = await client.post(
                "/api/v1/messages",
                json={"receiver_id": patient_id, "content": "읽음 처리 테스트"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
            message_id = send_response.json()["id"]

            # 환자가 메시지 조회 → 읽음 처리
            get_response = await client.get(
                f"/api/v1/messages/{message_id}", headers={"Authorization": f"Bearer {patient_token}"}
            )
            unread_response = await client.get(
                "/api/v1/messages/unread-count", headers={"Authorization": f"Bearer {patient_token}"}
            )
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["is_read"] is True
        assert unread_response.json()["count"] == 0

    async def test_get_message_unauthorized_user_forbidden(self):
        _, doctor_token = await self._create_doctor("msg_doc10@example.com", "01011110010")
        patient_id, _ = await self._create_patient("msg_pat10@example.com", "01022220010")
        _, outsider_token = await self._create_patient("msg_outsider@example.com", "01033330010")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            send_response = await client.post(
                "/api/v1/messages",
                json={"receiver_id": patient_id, "content": "제3자 접근 금지"},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
            message_id = send_response.json()["id"]

            response = await client.get(
                f"/api/v1/messages/{message_id}", headers={"Authorization": f"Bearer {outsider_token}"}
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN
