# Selenium 공식 이미지 (Chrome 포함)
FROM selenium/standalone-chrome:latest

# Python 설치
USER root
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 패키지 설치
COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY backend /app

# 포트 설정
EXPOSE 8000

# 서버 시작
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
