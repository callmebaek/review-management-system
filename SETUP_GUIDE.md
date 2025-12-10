# 🚀 리뷰 관리 시스템 설정 가이드

이 가이드는 리뷰 관리 시스템을 처음 설정하는 방법을 단계별로 설명합니다.

## 📋 사전 요구사항

- Python 3.9 이상
- Node.js 18 이상
- Google Cloud Platform 계정
- OpenAI API 계정

---

## 1️⃣ Google Cloud Console 설정

### 1.1 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com)에 접속
2. 상단의 프로젝트 선택 드롭다운 클릭
3. "새 프로젝트" 클릭
4. 프로젝트 이름 입력 (예: "review-management")
5. "만들기" 클릭

### 1.2 필수 API 활성화

1. 좌측 메뉴에서 "API 및 서비스" → "라이브러리" 클릭
2. 다음 API들을 검색하여 활성화:

   **필수 API:**
   - **Google My Business API**
   - **Google My Business Account Management API**
   - **Google My Business Business Information API**

   각 API를 클릭한 후 "사용 설정" 버튼을 누릅니다.

### 1.3 OAuth 2.0 클라이언트 ID 생성

1. "API 및 서비스" → "사용자 인증 정보" 클릭
2. 상단의 "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID" 클릭
3. 동의 화면 구성이 필요하다고 나오면:
   
   **동의 화면 구성:**
   - "외부" 선택 (테스트용)
   - 앱 이름: "리뷰 관리 시스템"
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일
   - "저장 후 계속" 클릭
   
   **범위 추가:**
   - "범위 추가 또는 삭제" 클릭
   - 검색창에 "business" 입력
   - `https://www.googleapis.com/auth/business.manage` 선택
   - "업데이트" 클릭
   - "저장 후 계속" 클릭
   
   **테스트 사용자:**
   - "+ ADD USERS" 클릭
   - GBP 계정 이메일 추가
   - "저장 후 계속" 클릭

4. "사용자 인증 정보" 탭으로 돌아가기
5. "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
6. 애플리케이션 유형: **웹 애플리케이션**
7. 이름: "Review Management Web Client"
8. **승인된 리디렉션 URI** 섹션에서 "URI 추가":
   ```
   http://localhost:8000/auth/google/callback
   ```
9. "만들기" 클릭
10. **클라이언트 ID**와 **클라이언트 보안 비밀번호**를 복사하여 안전한 곳에 저장

---

## 2️⃣ OpenAI API 키 발급

1. [OpenAI Platform](https://platform.openai.com)에 로그인
2. 우측 상단 프로필 아이콘 → "API keys" 클릭
3. "+ Create new secret key" 클릭
4. 키 이름 입력 (예: "review-management")
5. 생성된 API 키를 복사하여 안전한 곳에 저장
   ⚠️ **주의**: API 키는 한 번만 표시되므로 반드시 복사해두세요!

---

## 3️⃣ 프로젝트 설정

### 3.1 저장소 클론 및 의존성 설치

```bash
# 저장소 클론
cd review-machine

# 백엔드 의존성 설치
cd backend
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Python 패키지 설치
pip install -r requirements.txt

# 프론트엔드 의존성 설치
cd ../frontend
npm install
```

### 3.2 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성합니다:

```bash
# 프로젝트 루트로 이동
cd ..

# .env 파일 생성 (Windows)
type nul > .env

# .env 파일 생성 (macOS/Linux)
touch .env
```

`.env` 파일을 열고 다음 내용을 입력합니다:

```env
# Google Business Profile
GOOGLE_CLIENT_ID=여기에_구글_클라이언트_ID_입력
GOOGLE_CLIENT_SECRET=여기에_구글_클라이언트_시크릿_입력
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# OpenAI
OPENAI_API_KEY=여기에_OpenAI_API_키_입력
OPENAI_MODEL=gpt-4

# Server
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

⚠️ **중요**: 
- `GOOGLE_CLIENT_ID`와 `GOOGLE_CLIENT_SECRET`에 1.3단계에서 복사한 값을 입력
- `OPENAI_API_KEY`에 2단계에서 복사한 값을 입력
- `.env` 파일을 절대 Git에 커밋하지 마세요!

---

## 4️⃣ 애플리케이션 실행

### 4.1 백엔드 서버 실행

```bash
# backend 디렉토리로 이동
cd backend

# 가상환경이 활성화되어 있는지 확인
# (venv) 표시가 터미널에 나타나야 함

# FastAPI 서버 실행
python -m backend.main

# 또는
uvicorn backend.main:app --reload --port 8000
```

서버가 정상적으로 시작되면:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

브라우저에서 http://localhost:8000 접속하여 확인

### 4.2 프론트엔드 실행 (새 터미널)

```bash
# frontend 디렉토리로 이동
cd frontend

# 개발 서버 실행
npm run dev
```

프론트엔드가 정상적으로 시작되면:
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

브라우저에서 http://localhost:5173 접속

---

## 5️⃣ 첫 로그인 및 테스트

### 5.1 Google 계정 연결

1. http://localhost:5173 접속
2. "Google 계정으로 로그인" 버튼 클릭
3. Google 로그인 페이지로 리디렉션됨
4. GBP 계정으로 로그인
5. 권한 요청 화면에서 "허용" 클릭
6. 대시보드로 리디렉션됨

### 5.2 매장 확인

- 대시보드에 Google Business Profile의 매장 목록이 표시됨
- 각 매장 카드를 클릭하여 리뷰 관리 페이지로 이동

### 5.3 리뷰 관리 테스트

1. 매장 카드 클릭 → 리뷰 목록 확인
2. "답글 작성" 버튼 클릭
3. "AI 답글 생성" 버튼으로 자동 생성 테스트
4. 생성된 답글 확인 및 수정
5. "답글 게시" 버튼으로 발행

---

## 🔧 문제 해결

### 백엔드가 시작되지 않을 때

**문제**: `ModuleNotFoundError`
```bash
# 가상환경 활성화 확인
which python  # macOS/Linux
where python  # Windows

# 의존성 재설치
pip install -r requirements.txt
```

**문제**: Google OAuth 에러
- `.env` 파일의 `GOOGLE_CLIENT_ID`와 `GOOGLE_CLIENT_SECRET` 확인
- Google Cloud Console에서 리디렉션 URI 확인

### 프론트엔드가 백엔드와 통신하지 못할 때

**문제**: CORS 에러
- 백엔드가 http://localhost:8000에서 실행 중인지 확인
- `backend/main.py`의 CORS 설정 확인

**문제**: API 호출 실패
```bash
# 백엔드 health check
curl http://localhost:8000/health

# 응답 예시:
# {"status":"healthy","gbp_configured":true,"openai_configured":true}
```

### 리뷰를 불러올 수 없을 때

**가능한 원인**:
1. Google My Business API가 활성화되지 않음
2. OAuth 범위에 `business.manage`가 포함되지 않음
3. GBP 계정에 해당 매장의 접근 권한이 없음

**해결 방법**:
1. Google Cloud Console에서 API 활성화 확인
2. 로그아웃 후 재로그인하여 OAuth 재인증
3. Google Business Profile에서 계정 권한 확인

---

## 📚 추가 리소스

- [Google My Business API 문서](https://developers.google.com/my-business/content/overview)
- [OpenAI API 문서](https://platform.openai.com/docs)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [React 문서](https://react.dev/)

---

## ✅ 체크리스트

설정이 완료되었는지 확인하세요:

- [ ] Google Cloud Console 프로젝트 생성
- [ ] My Business API 3개 활성화
- [ ] OAuth 2.0 클라이언트 ID 생성
- [ ] OAuth 동의 화면 구성 및 테스트 사용자 추가
- [ ] OpenAI API 키 발급
- [ ] `.env` 파일 생성 및 모든 키 입력
- [ ] Python 가상환경 생성 및 의존성 설치
- [ ] Node.js 의존성 설치
- [ ] 백엔드 서버 정상 실행 (http://localhost:8000)
- [ ] 프론트엔드 정상 실행 (http://localhost:5173)
- [ ] Google 계정 연결 성공
- [ ] 매장 목록 표시 확인
- [ ] 리뷰 조회 성공
- [ ] AI 답글 생성 성공
- [ ] 답글 게시 성공

모든 항목이 체크되었다면 설정이 완료되었습니다! 🎉








