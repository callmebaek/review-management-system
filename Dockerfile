# Heroku용 Python 이미지
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
# Chromium과 Chrome Driver 설치 (Selenium/Playwright용)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY backend/requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치
RUN playwright install --with-deps chromium

# 애플리케이션 코드 복사
COPY backend /app

# Heroku는 동적 PORT 환경 변수 사용
EXPOSE $PORT

# 서버 시작 명령
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
