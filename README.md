# 🏥 AI Healthcare Service

AI 기반 의료 정보 서비스입니다. 의사가 진료 기록과 처방전을 입력하면, AI가 환자에게 맞춤형 복약 안내와 생활습관 가이드를 자동 생성합니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| **복약 알림** | 매일 오전 8시, 복약 중인 환자에게 이메일 알림 자동 발송 |
| **건강 일지** | 환자가 매일 통증 수치·기분·증상을 기록, AI가 회복 추이 분석 |
| **AI 가이드 스트리밍** | Gemini AI가 복약 안내·생활습관 가이드를 실시간 스트리밍으로 생성 |
| **메시지 채널** | 의사-환자 간 진료 기반 메시지 주고받기 |
| **JWT 인증** | Access Token + Redis 기반 Refresh Token (로그아웃 시 즉시 무효화) |

---

## 🛠 기술 스택

```
Backend   : FastAPI + Tortoise ORM + MySQL
AI Worker : Celery + Google Gemini API
Scheduler : Celery Beat (매일 복약 알림)
Cache     : Redis (Celery 브로커 + Refresh Token 저장)
Email     : Gmail SMTP (aiosmtplib)
Frontend  : Next.js
Infra     : Docker Compose + Nginx + AWS EC2
```

---

## 📂 프로젝트 구조

```
.
├── app/                        # FastAPI 서버
│   ├── apis/v1/                # API 라우터
│   │   ├── auth_routers.py     # 회원가입·로그인·로그아웃·토큰 갱신
│   │   ├── record_routers.py   # 진료 기록 CRUD + 가이드·일지·메시지
│   │   ├── guide_routers.py    # AI 가이드 조회
│   │   ├── health_log_routers.py # 건강 일지 CRUD + AI 분석
│   │   ├── message_routers.py  # 메시지 채널
│   │   └── user_routers.py     # 유저 정보
│   ├── models/                 # DB 모델
│   │   ├── users.py            # User (DOCTOR / PATIENT)
│   │   ├── records.py          # MedicalRecord, Prescription
│   │   ├── guides.py           # Guide (AI 가이드)
│   │   ├── health_logs.py      # HealthLog, HealthLogAnalysis
│   │   └── messages.py         # Message
│   ├── core/
│   │   ├── jwt/                # JWT 발급·검증
│   │   └── redis.py            # async Redis 클라이언트
│   └── services/               # 비즈니스 로직
├── ai_worker/                  # Celery Worker
│   └── tasks/
│       ├── generate_guide.py           # AI 가이드 생성
│       ├── send_medication_reminder.py # 복약 알림 이메일
│       └── analyze_health_logs.py      # 건강 일지 AI 분석
├── frontend/                   # Next.js 프론트엔드
├── infra/                      # Nginx 설정
├── scripts/                    # 배포·CI 스크립트
├── envs/                       # 환경변수 예시 파일
└── docker-compose.yml          # 로컬 전체 스택 실행
```

---

## ⚙️ 시작하기

### 1. 환경변수 설정

```bash
cp envs/example.local.env envs/.local.env
```

`envs/.local.env` 파일을 열어 아래 항목을 채워주세요.

```env
# DB
DB_HOST=localhost
DB_USER=ozcoding
DB_PASSWORD=pw1234
DB_NAME=ai_health

# Redis
REDIS_URL=redis://localhost:6379/2
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AI
GEMINI_API_KEY=your-gemini-api-key

# 이메일 (Gmail 앱 비밀번호)
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# JWT
SECRET_KEY=your-secret-key
```

> **Gmail 앱 비밀번호 발급**: Google 계정 → 보안 → 2단계 인증 활성화 → 앱 비밀번호 생성

### 2. 전체 스택 실행 (Docker)

```bash
docker-compose up -d --build
```

| 서비스 | 주소 |
|--------|------|
| API Swagger | http://localhost/api/docs |
| API ReDoc | http://localhost/api/redoc |

### 3. 로컬 개별 실행

```bash
# 의존성 설치
uv sync --group app --group ai

# FastAPI 서버
uv run uvicorn app.main:app --reload

# Celery Worker
uv run celery -A ai_worker.main worker --loglevel=info

# Celery Beat (복약 알림 스케줄러)
uv run celery -A ai_worker.main beat --loglevel=info
```

---

## 📡 API 엔드포인트

### 인증 `/api/v1/auth`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/auth/signup` | 회원가입 | - |
| POST | `/auth/login` | 로그인 (Access + Refresh Token 발급) | - |
| POST | `/auth/logout` | 로그아웃 (Refresh Token 즉시 무효화) | 로그인 |
| GET | `/auth/token/refresh` | Access Token 갱신 | Refresh Token |

### 진료 기록 `/api/v1/records`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/records` | 진료 기록 + 처방전 생성 | 의사 |
| GET | `/records` | 내 진료 기록 목록 | 의사·환자 |
| GET | `/records/{id}` | 진료 기록 상세 | 의사·환자 |
| POST | `/records/{id}/guides` | AI 가이드 생성 요청 (Celery 비동기) | 환자 |
| POST | `/records/{id}/guides/stream` | AI 가이드 실시간 스트리밍 생성 | 환자 |
| GET | `/records/{id}/guides` | 가이드 목록 조회 | 의사·환자 |
| GET | `/records/{id}/health-logs` | 진료별 건강 일지 조회 | 의사·환자 |
| GET | `/records/{id}/messages` | 진료별 메시지 스레드 | 의사·환자 |

### 건강 일지 `/api/v1/health-logs`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/health-logs` | 일지 작성 (통증 0~10, 기분, 증상) | 환자 |
| GET | `/health-logs` | 내 일지 전체 조회 | 환자 |
| GET | `/health-logs/{id}` | 일지 상세 | 의사·환자 |
| DELETE | `/health-logs/{id}` | 일지 삭제 | 환자 |
| POST | `/health-logs/analyze` | AI 회복 분석 요청 | 환자 |
| GET | `/health-logs/analyses/{id}` | 분석 결과 조회 | 환자 |

### 메시지 `/api/v1/messages`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/messages` | 메시지 전송 | 의사·환자 |
| GET | `/messages/inbox` | 받은 메시지함 | 의사·환자 |
| GET | `/messages/sent` | 보낸 메시지함 | 의사·환자 |
| GET | `/messages/unread-count` | 안 읽은 메시지 수 | 의사·환자 |
| GET | `/messages/{id}` | 상세 조회 + 자동 읽음 처리 | 의사·환자 |

---

## 🔐 인증 방식

```
로그인 → Access Token (헤더) + Refresh Token (httponly 쿠키)

API 요청:
  Authorization: Bearer <access_token>

토큰 갱신:
  GET /auth/token/refresh  (쿠키 자동 전송)

로그아웃:
  POST /auth/logout → Redis에서 Refresh Token 즉시 삭제
```

---

## 📊 AI 기능 상세

### 복약 안내 + 생활습관 가이드

```
환자 요청
  └→ Guide 생성 (PENDING)
       └→ Celery Task → Gemini API 호출
            └→ Guide 업데이트 (COMPLETED)
                 ├ medication_guide  : 약물별 복용법·부작용
                 └ lifestyle_guide   : 식단·운동·수면 조언
```

또는 **스트리밍** 방식으로 즉시 타이핑 효과와 함께 수신:
```
POST /records/{id}/guides/stream
  └→ SSE (text/event-stream)
       ├ data: {"type": "chunk", "text": "..."}  # 실시간 청크
       └ data: {"type": "done", "guide_id": 42}  # 완료
```

### 건강 일지 AI 분석

```
일지 목록 (통증 추이·기분·증상)
  └→ Celery Task → Gemini API
       └→ 분석 결과 3파트
            ├ 전반적인 회복 추이
            ├ 증상 변화 분석
            └ 권장 사항
```

### 복약 알림 이메일

```
Celery Beat (매일 오전 8시)
  └→ DB 조회: 오늘 복약 중인 환자
       └→ Gmail SMTP → 환자 이메일 발송
```

---

## 🧪 품질 관리

```bash
# 테스트
./scripts/ci/run_test.sh

# 코드 포맷 (Ruff)
./scripts/ci/code_fommatting.sh

# 타입 체크 (Mypy)
./scripts/ci/check_mypy.sh
```

---

## 🚀 EC2 배포

```bash
# 배포 스크립트 (이미지 빌드 → Docker Hub push → EC2 배포)
chmod +x scripts/deployment.sh
./scripts/deployment.sh

# SSL 인증서 발급 (Let's Encrypt)
chmod +x scripts/certbot.sh
./scripts/certbot.sh
```

---

## 📝 개발 가이드

- **API 추가**: `app/apis/v1/` 에 라우터 파일 생성 → `app/apis/v1/__init__.py` 에 등록
- **DB 모델 추가**: `app/models/` 에 모델 정의 → `app/core/db/databases.py` MODELS 리스트 추가 → `aerich migrate`
- **AI 태스크 추가**: `ai_worker/tasks/` 에 `@shared_task` 작성 → `ai_worker/main.py` include 등록