# 🏃 빠른 실행 가이드

이미 설정을 완료했다면, 이 가이드를 따라 애플리케이션을 실행하세요.

## 🚀 실행 방법

### 1단계: 백엔드 서버 실행

```bash
# 프로젝트 루트에서
cd backend

# 가상환경 활성화
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# FastAPI 서버 실행
python -m backend.main
```

**확인**: 터미널에 다음과 같은 메시지가 표시되어야 합니다.
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

브라우저에서 http://localhost:8000 접속하여 API가 작동하는지 확인하세요.

### 2단계: 프론트엔드 실행 (새 터미널)

```bash
# 프로젝트 루트에서
cd frontend

# 개발 서버 실행
npm run dev
```

**확인**: 터미널에 다음과 같은 메시지가 표시되어야 합니다.
```
  VITE v5.0.11  ready in 500 ms
  ➜  Local:   http://localhost:5173/
```

브라우저에서 http://localhost:5173 접속하세요.

---

## ✅ 정상 작동 확인

1. **로그인 페이지** (`/login`)
   - "Google 계정으로 로그인" 버튼이 보여야 함
   - 버튼 클릭 시 Google OAuth 페이지로 리디렉션

2. **대시보드** (`/dashboard`)
   - Google 인증 후 자동으로 리디렉션
   - 매장 목록이 카드 형태로 표시
   - 각 매장의 이름, 주소, 전화번호 확인

3. **리뷰 관리** (`/reviews`)
   - 매장 카드 클릭 시 리뷰 목록 페이지로 이동
   - 필터 기능 (전체/미답변/답변완료)
   - 각 리뷰에 "답글 작성" 버튼
   - "AI 답글 생성" 및 "답글 게시" 기능

4. **설정** (`/settings`)
   - Google 계정 연결 상태 확인
   - 프롬프트 템플릿 확인

---

## 🛑 종료 방법

### 백엔드 종료
백엔드 터미널에서 `Ctrl + C` 입력

### 프론트엔드 종료
프론트엔드 터미널에서 `Ctrl + C` 입력

---

## 🔄 재시작이 필요한 경우

### 백엔드 코드 변경 시
- `--reload` 플래그로 실행했다면 자동 재시작됨
- 그렇지 않다면 `Ctrl + C` 후 다시 실행

### 프론트엔드 코드 변경 시
- Vite가 자동으로 Hot Module Replacement (HMR) 적용
- 브라우저가 자동 새로고침됨

### 환경 변수(.env) 변경 시
- 백엔드 서버를 재시작해야 함
- `Ctrl + C` 후 다시 실행

### 의존성 변경 시
**백엔드**:
```bash
pip install -r requirements.txt
```

**프론트엔드**:
```bash
npm install
```

---

## 🐛 일반적인 문제

### "가상환경을 찾을 수 없습니다"
```bash
# backend 디렉토리에서
python -m venv venv
```

### "Module not found" 에러
```bash
# backend 디렉토리에서
pip install -r requirements.txt
```

### 포트가 이미 사용 중
**백엔드 (8000 포트)**:
```bash
# 포트 변경하여 실행
uvicorn backend.main:app --reload --port 8001
```

**프론트엔드 (5173 포트)**:
```bash
# vite.config.js에서 포트 변경
# 또는
npm run dev -- --port 3000
```

### CORS 에러
- 백엔드가 정상 실행 중인지 확인
- `backend/main.py`의 CORS 설정 확인
- 브라우저 캐시 삭제 후 재시도

---

## 📊 API 테스트 (선택사항)

Swagger UI를 통해 API를 테스트할 수 있습니다:

1. 백엔드 서버 실행
2. http://localhost:8000/docs 접속
3. 각 엔드포인트 테스트

주요 엔드포인트:
- `GET /health` - 서버 상태 확인
- `GET /auth/google/login` - OAuth 시작
- `GET /api/gbp/accounts` - GBP 계정 목록
- `GET /api/gbp/locations` - 매장 목록
- `GET /api/gbp/reviews` - 리뷰 목록
- `POST /api/reviews/generate-reply` - AI 답글 생성

---

## 💡 팁

### 개발 효율성
- 백엔드와 프론트엔드를 별도 터미널에서 실행
- IDE의 통합 터미널 기능 활용
- VS Code의 경우 터미널 분할 기능 사용

### 로그 확인
- 백엔드: 터미널에 API 요청/응답 로그 출력
- 프론트엔드: 브라우저 개발자 도구(F12) → Console 탭

### 디버깅
- 백엔드: `print()` 또는 `logging` 사용
- 프론트엔드: `console.log()` 사용
- Chrome DevTools의 Network 탭으로 API 호출 확인

---

## 🎯 다음 단계

Stage 1 (GBP)이 완료되었습니다!

다음은 Stage 2 (네이버 플레이스) 구현을 진행할 수 있습니다.








