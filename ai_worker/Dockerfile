FROM python:3.13-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 2. 의존성 패키지 관리 파일 복사
COPY pyproject.toml uv.lock ./

# 3. ai + app 그룹 패키지 설치 (워커는 app 모델도 임포트하므로 둘 다 필요)
RUN uv sync --group ai --group app --no-dev --frozen

# 4. 소스 코드 복사 (app 모델을 임포트하므로 두 디렉토리 모두 필요)
COPY ./app ./app
COPY ./ai_worker ./ai_worker

# 5. Celery 워커 실행
CMD ["uv", "run", "--no-sync", "celery", "-A", "ai_worker.main", "worker", "--loglevel=info"]
