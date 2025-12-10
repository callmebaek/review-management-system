# Python 베이스 이미지
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# Python 패키지 설치 (Playwright 제외)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY backend /app

# 포트 설정
EXPOSE 8000

# 서버 시작
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
