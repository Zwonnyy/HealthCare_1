# 🏥 MediGuide AI

AI 기반 의사-환자 건강관리 플랫폼입니다. 의사가 진료 기록과 처방전을 등록하면 환자는 AI 복약 가이드, 건강 인사이트, 복약 체크, 진료 전 문진, 건강 목표 관리를 받을 수 있고, 의사는 환자 위험도 큐와 타임라인으로 진료 전후 상태를 빠르게 파악할 수 있습니다.

---

## 📌 포트폴리오 요약

| 항목 | 내용 |
|------|------|
| **프로젝트 목적** | 진료 후 환자 관리 공백을 줄이고, 의사가 환자 상태 변화를 한눈에 볼 수 있는 AI 헬스케어 서비스 구현 |
| **주요 사용자** | 환자, 의사 |
| **핵심 가치** | AI 안내, RAG 증상 분석, 복약 관리, 위험 신호 알림, 의사용 환자 모니터링 |
| **개발 범위** | 백엔드 API, 프론트엔드, 인증, DB 모델링, AI 연동, 비동기 작업, CI/CD, 배포 설정 |
| **기술 키워드** | FastAPI, Next.js, MySQL, Redis, Celery, Qdrant, Gemini API, JWT, GitHub Actions, Docker |

### 문제 정의

- 진료 후 환자가 복약법과 생활관리 지침을 잊거나 꾸준히 실천하지 못하는 문제가 있습니다.
- 의사는 환자의 건강일지, 바이탈, 증상 체크, 문진 내용을 여러 화면에서 확인해야 해 진료 전 상태 파악이 어렵습니다.
- 환자의 위험 신호가 누적되어도 의료진에게 빠르게 전달되지 않으면 대응이 늦어질 수 있습니다.

### 해결 방향

- 진료기록과 처방전을 기반으로 환자 맞춤형 AI 복약/생활 가이드를 생성합니다.
- 건강일지, 바이탈, 증상 체크, 복약 체크를 통합 분석해 건강 리스크와 누락 패턴을 제공합니다.
- 의사용 환자 위험도 큐와 타임라인을 제공해 위험 환자를 우선 확인할 수 있게 했습니다.
- 예약 전 문진을 AI가 요약하고 SOAP 진료 메모 초안을 생성해 진료 준비 시간을 줄입니다.

### 포트폴리오 핵심 어필 포인트

| 구분 | 구현 내용 |
|------|-----------|
| **AI/RAG** | Gemini API와 Qdrant 벡터 검색을 활용한 복약 가이드, 증상 체크, 약물 상호작용 분석 |
| **백엔드 설계** | FastAPI 라우터/서비스/레포지토리 계층 분리, Tortoise ORM 기반 MySQL 모델링 |
| **비동기 처리** | Celery + Redis로 AI 가이드 생성, 건강일지 분석, 복약 알림 스케줄링 처리 |
| **인증/보안** | JWT Access Token + Redis Refresh Token 구조, 역할 기반 의사/환자 권한 분리 |
| **프론트엔드** | Next.js App Router 기반 역할별 화면, 차트, 건강 인사이트, 문진/타임라인 UI |
| **품질 관리** | GitHub Actions에서 Ruff lint/format, pytest coverage 실행. Vercel 빌드 타입 오류 수정 경험 포함 |

### 대표 시나리오

```text
1. 의사가 환자 진료기록과 처방전을 등록
2. 환자는 AI 복약 가이드와 진료 후 액션 플랜 확인
3. 환자가 복약 체크, 바이탈, 건강일지, 증상 체크를 기록
4. AI 건강 인사이트가 리스크와 복약 누락 패턴을 분석
5. 리스크가 높으면 환자와 담당 의사에게 알림 생성
6. 의사는 위험도 큐와 환자 타임라인으로 우선 확인할 환자를 선별
7. 다음 진료 전 환자는 문진을 작성하고, 의사는 AI 요약과 SOAP 메모 초안을 확인
```

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| **AI 가이드 자동 생성** | 진료기록·처방전 기반으로 Gemini AI가 복약 안내·생활습관 가이드 생성 (Celery 비동기) |
| **RAG 기반 증상 체크** | 의학 가이드라인 벡터 검색 + Gemini AI로 긴급도 평가 및 진료 예약 권고 |
| **바이탈 AI 이상 감지** | 혈압·혈당·심박수 입력 시 Gemini가 실시간으로 정상 범위 대비 이상 여부 판단 |
| **약물 상호작용 검사** | 복용 약물 목록을 입력하면 RAG + Gemini로 상호작용 위험 분석 |
| **복약 알림 스케줄러** | Celery Beat 매 분 체크 — 설정 시각에 자동 인앱 알림 발송 (하루 1회 보장) |
| **AI 건강 인사이트** | 건강 리스크 예측, 복약 순응도, 복약 누락 패턴 분석을 한 화면에서 제공 |
| **진료 전 AI 문진** | 환자가 예약 전 문진을 작성하면 Gemini가 의사용 요약과 SOAP 진료 메모 초안 생성 |
| **의사용 환자 타임라인** | 진료기록·바이탈·건강일지·증상체크·문진 요약을 시간순으로 통합 조회 |
| **의사용 환자 위험도 큐** | 담당 환자의 건강 리스크를 높음/주의/낮음 순으로 정렬해 우선 확인 |
| **진료 후 액션 플랜** | 진료기록·처방·의사 메모 기반으로 환자 체크리스트 자동 생성 |
| **위험 신호 자동 알림** | 건강 리스크가 주의/높음이면 환자와 담당 의사에게 중복 방지 알림 생성 |
| **건강 일지 & AI 분석** | 매일 통증·기분·증상 기록, AI가 회복 추이 분석 |
| **맞춤 건강 목표 추천** | 최근 바이탈·통증·복약 기록 기반으로 개인화 목표 추천 및 즉시 생성 |
| **건강 리포트 PDF** | 월별 건강 리포트 브라우저 인쇄/PDF 저장 |
| **예약 관리** | 환자가 의사에게 예약 요청, 의사가 확정/취소 처리 |
| **통계 대시보드** | 통증 추이 차트(recharts), 기분 분포 차트, 바이탈 추이 시각화 |
| **메시지 채널** | 의사-환자 간 진료 기반 메시지 주고받기 |
| **알림 센터** | 새 메시지·예약·AI 가이드 완료 시 자동 인앱 알림 생성 |
| **프로필 이미지 업로드** | JPG/PNG/WEBP 프로필 이미지를 업로드하고 Navbar·프로필 화면에 표시 |
| **JWT 인증** | Access Token + Redis 기반 Refresh Token (로그아웃 시 즉시 무효화) |

---

## 🛠 기술 스택

```
Backend   : FastAPI + Tortoise ORM + MySQL + Aerich (마이그레이션)
AI        : Google Gemini API (gemini-flash-latest, gemini-embedding-001)
Vector DB : Qdrant (RAG 파이프라인)
AI Worker : Celery + Redis (비동기 AI 태스크)
Scheduler : Celery Beat (복약 알림 매 분 체크)
Frontend  : Next.js 16 + React 19 + Tailwind CSS + shadcn/ui + recharts
Infra     : Docker Compose + Nginx + AWS EC2
CI/CD     : GitHub Actions (ruff lint/format + pytest), Vercel Frontend Build
```

---

## 🧭 아키텍처

```text
Next.js Frontend
  ├ 환자 화면: 대시보드, 복약 체크, 건강 인사이트, 문진, 목표, 리포트
  └ 의사 화면: 진료기록, 환자 위험도 큐, 타임라인, 문진 요약

FastAPI Backend
  ├ Auth/JWT/Redis Refresh Token
  ├ Records/Appointments/Messages/Notifications
  ├ Health Logs/Vitals/Symptom Checks/Medication Checks
  ├ Health Insights/Risk Queue/Action Plan
  └ AI Services
       ├ Gemini API
       ├ Qdrant RAG
       └ Celery Worker + Redis Broker

MySQL
  └ Users, Records, Prescriptions, HealthLogs, Vitals, Reminders, Appointments, Notifications ...
```

---

## 📂 프로젝트 구조

```
.
├── app/                        # FastAPI 서버
│   ├── apis/v1/                # API 라우터 (20개)
│   │   ├── auth_routers.py     # 회원가입·로그인·토큰 갱신
│   │   ├── record_routers.py   # 진료 기록 CRUD
│   │   ├── guide_routers.py    # AI 가이드 조회
│   │   ├── vital_routers.py    # 바이탈 기록 + AI 이상 감지
│   │   ├── symptom_check_routers.py  # AI 증상 체크
│   │   ├── appointment_routers.py    # 예약 관리
│   │   ├── reminder_routers.py       # 복약 알림 설정
│   │   ├── health_log_routers.py     # 건강 일지 + AI 분석
│   │   ├── health_goal_routers.py    # 건강 목표 관리
│   │   ├── health_insight_routers.py # AI 건강 인사이트·문진·타임라인
│   │   ├── health_report_routers.py  # 건강 리포트 PDF
│   │   ├── drug_interaction_routers.py # 약물 상호작용
│   │   ├── stats_routers.py    # 통계/대시보드
│   │   ├── message_routers.py  # 메시지 채널
│   │   ├── notification_routers.py   # 알림 센터
│   │   └── ...
│   ├── models/                 # DB 모델 (16개)
│   │   ├── users.py            # User (DOCTOR / PATIENT)
│   │   ├── records.py          # MedicalRecord, Prescription
│   │   ├── vitals.py           # VitalRecord
│   │   ├── symptom_checks.py   # SymptomCheck
│   │   ├── medication_reminders.py   # MedicationReminder
│   │   ├── appointments.py     # Appointment
│   │   ├── pre_visit_questionnaires.py # 진료 전 문진
│   │   └── ...
│   ├── services/               # 비즈니스 로직 + AI 연동
│   │   ├── vitals.py           # Gemini 이상 감지
│   │   ├── symptom_checks.py   # RAG + Gemini 증상 분석
│   │   ├── medication_reminders.py   # 알림 발송 로직
│   │   ├── health_insights.py  # 건강 리스크·문진 요약·타임라인·복약 패턴
│   │   ├── health_goals.py     # 목표 CRUD + 맞춤 추천
│   │   └── rag/                # RAG 파이프라인
│   │       ├── guideline_rag.py  # 의학 가이드라인 검색
│   │       ├── drug_rag.py       # 약물 정보 검색
│   │       └── patient_rag.py    # 환자 진료기록 검색
│   └── tests/                  # pytest 테스트 (9개 모듈)
├── ai_worker/                  # Celery Worker
│   └── tasks/
│       ├── generate_guide.py             # AI 가이드 생성
│       ├── analyze_health_logs.py        # 건강 일지 AI 분석
│       └── check_medication_reminders.py # 복약 알림 체크 (매 분)
├── frontend/                   # Next.js 프론트엔드 (20개 페이지)
│   └── app/
│       ├── dashboard/          # 통계 차트 대시보드
│       ├── vitals/             # 바이탈 기록 + 추이 차트
│       ├── symptom-check/      # AI 증상 체크
│       ├── reminders/          # 복약 알림 설정
│       ├── health-insights/    # AI 건강 인사이트·문진·의사용 타임라인
│       ├── health-goals/goals/ # 건강 목표 + 맞춤 추천
│       ├── appointments/       # 예약 관리
│       └── ...
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

### 2. 백엔드 스택 실행 (Docker)

```bash
docker-compose up -d --build
```

| 서비스 | 주소 |
|--------|------|
| API Swagger | http://localhost/api/docs |
| API ReDoc | http://localhost/api/redoc |

프론트엔드는 별도 터미널에서 실행합니다.

```bash
cd frontend
npm install
npm run dev
```

| 서비스 | 주소 |
|--------|------|
| 프론트엔드 (Next.js) | http://localhost:3000 |

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
| GET | `/records/{id}/action-plan` | 진료 후 환자 액션 플랜 조회 | 의사·환자 |

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

### 알림 `/api/v1/notifications`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/notifications` | 내 알림 목록 (페이지네이션) | 의사·환자 |
| GET | `/notifications/unread-count` | 미읽은 알림 수 | 의사·환자 |
| PATCH | `/notifications/{id}/read` | 개별 읽음 처리 | 의사·환자 |
| PATCH | `/notifications/read-all` | 전체 읽음 처리 | 의사·환자 |

### AI 건강 인사이트 `/api/v1/health-insights`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/health-insights/risk` | 최근 건강일지·바이탈·증상체크 기반 건강 리스크 산정 + 위험 알림 자동 생성 | 환자 |
| GET | `/health-insights/medication-adherence` | 처방 기간 대비 복약 체크율 분석 | 환자 |
| GET | `/health-insights/medication-patterns` | 요일별 복약 누락, 연속 누락, 개선 제안 분석 | 환자 |
| GET | `/health-insights/risk-queue` | 담당 환자 위험도 큐 조회 | 의사 |
| POST | `/health-insights/appointments/{appointment_id}/pre-visit` | 예약 전 문진 작성 + AI 요약 생성 | 환자 |
| GET | `/health-insights/pre-visits` | 문진 요약 목록 조회 | 의사·환자 |
| POST | `/health-insights/pre-visits/{pre_visit_id}/clinical-note-draft` | 문진 기반 SOAP 진료 메모 초안 생성 | 의사 |
| GET | `/health-insights/patients/{patient_id}/timeline` | 환자 진료·바이탈·일지·증상·문진 통합 타임라인 | 의사 |

### 건강 목표 `/api/v1/health-goals/goals`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/health-goals/goals` | 건강 목표 생성 | 환자 |
| GET | `/health-goals/goals` | 건강 목표 목록 조회 | 환자 |
| GET | `/health-goals/goals/recommendations` | 최근 건강 기록 기반 맞춤 목표 추천 | 환자 |
| PATCH | `/health-goals/goals/{id}` | 현재값·달성 여부 업데이트 | 환자 |
| DELETE | `/health-goals/goals/{id}` | 목표 삭제 | 환자 |
| GET | `/health-goals/goals/{id}/history` | 목표 진행 이력 조회 | 환자 |

### 사용자 `/api/v1/users`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/users/me` | 내 프로필 조회 | 의사·환자 |
| PATCH | `/users/me` | 내 프로필/비밀번호 수정 | 의사·환자 |
| POST | `/users/me/profile-image` | 프로필 이미지 업로드 (JPG/PNG/WEBP, 2MB 이하) | 의사·환자 |
| GET | `/users/patients/search` | 환자 검색 | 의사 |
| GET | `/users/doctors/search` | 의사 검색 | 환자 |

### 통계/대시보드 `/api/v1/stats`

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/stats/patient` | 환자 대시보드 통계 | 환자 |
| GET | `/stats/doctor` | 의사 대시보드 통계 | 의사 |

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

### 1. 복약 안내 + 생활습관 가이드

```
환자 요청
  └→ Guide 생성 (PENDING)
       └→ Celery Task → Gemini API 호출
            └→ Guide 업데이트 (COMPLETED)
                 ├ medication_guide  : 약물별 복용법·부작용
                 └ lifestyle_guide   : 식단·운동·수면 조언
```

### 2. RAG 기반 증상 체크

```
환자 증상 입력
  └→ Qdrant 벡터 검색 (의학 가이드라인)
       └→ 관련 문서 → Gemini 프롬프트 주입
            └→ JSON 응답
                 ├ urgency: LOW | MEDIUM | HIGH
                 ├ assessment: 증상 평가 (3-4문장)
                 ├ recommendation: 권고 사항
                 └ suggest_appointment: true | false
```

### 3. 바이탈 AI 이상 감지

```
혈압·혈당·심박수 입력
  └→ Gemini API (정상 범위 기준 판단)
       ├ 정상: alert_message = null
       └ 이상: alert_message = "혈압이 높습니다. 즉시 진료를 받으세요."
```

### 4. 복약 알림 스케줄러

```
Celery Beat (매 분 실행)
  └→ DB 조회: enabled=True, reminder_time == 현재 HH:MM, last_notified_date != 오늘
       └→ 알림 생성 + last_notified_date 갱신 (하루 1회 보장)
```

### 5. 건강 일지 AI 분석

```
일지 목록 (통증 추이·기분·증상)
  └→ Celery Task → Gemini API
       └→ 분석 결과 3파트
            ├ 전반적인 회복 추이
            ├ 증상 변화 분석
            └ 권장 사항
```

### 6. AI 건강 인사이트

```
최근 건강 데이터 수집
  ├ 건강일지: 통증 점수, 기분, 증상
  ├ 바이탈: 혈압, 혈당, 심박, 체중
  ├ 증상 체크: 긴급도, 진료 권고 여부
  └ 복약 체크: 처방 기간 대비 체크 기록
       └→ 리스크 점수·복약 순응도·요일별 누락 패턴 계산
            ├ risk_level: 낮음 | 주의 | 높음
            ├ 위험 신호 요약
            ├ 환자 행동 권고
            └ 주의/높음이면 환자·담당 의사에게 알림 생성
```

### 7. 진료 전 문진 + 진료 메모 초안

```
환자 예약 전 문진 작성
  └→ Gemini 요약 생성
       ├ 핵심 호소
       ├ 확인할 위험 신호
       ├ 의사가 물어볼 질문
       └ 환자 질문

의사 문진 확인
  └→ SOAP 형식 진료 메모 초안 생성
       ├ S: 주관적 증상
       ├ O: 문진 기반 객관 정보
       ├ A: 감별 필요 사항
       └ P: 확인/검사/추적 계획 초안
```

### 8. 의사용 위험도 큐 + 환자 타임라인

```text
담당 환자 목록 수집
  ├ 진료기록이 있는 환자
  └ 예약 이력이 있는 환자
       └→ 환자별 건강 리스크 계산
            ├ 높음/주의/낮음 정렬
            ├ 최근 활동 시각 표시
            └ 환자 선택 시 타임라인 조회

환자 타임라인
  ├ 진료기록
  ├ 건강일지
  ├ 바이탈 기록
  ├ 증상 체크
  └ 진료 전 문진
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

최근 검증 결과:

- `uv run ruff check .` 통과
- `uv run ruff format . --check` 통과
- `uv run coverage run -m pytest app` 61 passed
- `uv run coverage report -m` 통과
- `cd frontend && npm run build` 통과
- `cd frontend && npm run lint` 통과
  - Next.js `<img>` 최적화 관련 warning 2개는 남아 있음

---

## 🧯 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| **Vercel 빌드 실패** | `NotificationType`에 `HEALTH_RISK_ALERT`를 추가했지만 `Record<NotificationType, string>` 아이콘 매핑에서 누락 | 알림 페이지에 신규 타입 매핑을 추가하고 `npm run build` 통과 확인 |
| **GitHub Actions CI 실패** | 로컬 lint는 통과했지만 CI의 `ruff format . --check`에서 포맷 불일치 발생 | CI와 동일한 명령을 로컬에서 재현하고 Ruff format 적용 |
| **AI 응답 실패 가능성** | Gemini API 호출 실패 또는 JSON 응답 파싱 실패 가능 | 문진 요약과 SOAP 메모 초안 생성에 fallback 응답을 구현해 사용자 흐름 유지 |
| **알림 중복 생성** | 건강 리스크 API 조회마다 같은 위험 알림이 반복 생성될 수 있음 | 최근 24시간 동일 제목의 리스크 알림이 있으면 새로 생성하지 않도록 제한 |
| **복약 알림 중복 발송** | 스케줄러가 매 분 실행되면 같은 알림이 반복될 수 있음 | `last_notified_date`로 하루 1회만 발송되도록 제어 |

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
