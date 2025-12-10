# 리뷰 관리 시스템 (Review Management System)

Google Business Profile과 네이버 플레이스의 리뷰를 통합 관리하고, AI로 자동 답글을 생성하는 웹 기반 시스템입니다.

## 🚀 기능

### ✅ Stage 1: Google Business Profile (완료!)
- ✅ GBP OAuth 2.0 인증
- ✅ 매장(Location) 관리
- ✅ 리뷰 조회 (replied/unreplied 필터링)
- ✅ AI 답글 자동 생성 (OpenAI GPT-4)
- ✅ 답글 작성 및 관리
- ✅ 반응형 웹 UI (React + Tailwind CSS)
- ✅ 실시간 프롬프트 템플릿 관리

### ✅ Stage 2: 네이버 플레이스 (완료!)
- ✅ Playwright 웹 자동화
- ✅ 스마트플레이스 센터 리뷰 크롤링
- ✅ 답글 자동 작성 및 게시
- ✅ 프론트엔드 통합
- ✅ 세션 관리 및 Rate Limiting
- ⚠️ **주의**: 개인 사용 목적으로만 사용 (공식 API 미제공)

## 📋 사전 요구사항

- Python 3.9 이상
- Node.js 18 이상
- Google Cloud Platform 계정
- OpenAI API 키

## 📚 문서

- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - 처음 설정하는 경우 (상세 가이드)
- **[RUN_GUIDE.md](./RUN_GUIDE.md)** - 이미 설정을 완료한 경우 (빠른 실행)

---

## 🛠️ 설치 및 실행

### 1. 저장소 클론

```bash
git clone <repository-url>
cd review-machine
```

### 2. 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 필요한 값을 입력합니다:

```bash
cp .env.example .env
```

`.env` 파일 예시:
```
GOOGLE_CLIENT_ID=your_actual_client_id
GOOGLE_CLIENT_SECRET=your_actual_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

OPENAI_API_KEY=sk-your_actual_openai_key
OPENAI_MODEL=gpt-4

BACKEND_PORT=8000
FRONTEND_PORT=5173
```

### 4. Google Cloud Console 설정

#### 4.1 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성

#### 4.2 API 활성화
"API 및 서비스" → "라이브러리"에서 다음 API를 활성화:
- Google My Business API
- Google My Business Account Management API
- Google My Business Business Information API

#### 4.3 OAuth 2.0 클라이언트 ID 생성
1. "API 및 서비스" → "사용자 인증 정보"
2. "사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
3. 애플리케이션 유형: **웹 애플리케이션**
4. 승인된 리디렉션 URI: `http://localhost:8000/auth/google/callback`
5. 생성된 클라이언트 ID와 Secret을 `.env`에 저장

#### 4.4 OAuth 동의 화면 구성
1. "OAuth 동의 화면" 메뉴 선택
2. 사용자 유형: 외부 (테스트용) 선택
3. 범위 추가: `https://www.googleapis.com/auth/business.manage`

### 5. 백엔드 실행

```bash
# backend 디렉토리에서
python -m backend.main

# 또는
uvicorn backend.main:app --reload --port 8000
```

서버가 http://localhost:8000 에서 실행됩니다.

### 6. 프론트엔드 설정 및 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드가 http://localhost:5173 에서 실행됩니다.

## 📁 프로젝트 구조

```
review-machine/
├── backend/
│   ├── main.py                    # FastAPI 진입점
│   ├── config.py                  # 설정 관리
│   ├── requirements.txt
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py           # OAuth 인증
│   │       ├── gbp.py            # GBP API
│   │       └── reviews.py        # 리뷰 통합
│   ├── services/
│   │   ├── gbp_service.py        # GBP 비즈니스 로직
│   │   └── llm_service.py        # OpenAI 통합
│   ├── models/
│   │   └── schemas.py            # Pydantic 모델
│   └── utils/
│       └── token_manager.py      # 토큰 관리
├── frontend/
│   ├── src/
│   │   ├── pages/               # 페이지 컴포넌트
│   │   ├── components/          # 재사용 컴포넌트
│   │   └── api/                 # API 클라이언트
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── stores.json              # 매장 정보
│   ├── prompts.json             # LLM 프롬프트
│   └── tokens/                  # OAuth 토큰
├── .env                         # 환경 변수 (gitignore)
└── README.md
```

## 🔑 API 엔드포인트

### 인증
- `GET /auth/google/login` - GBP OAuth 시작
- `GET /auth/google/callback` - OAuth 콜백

### GBP
- `GET /api/gbp/accounts` - 계정 목록
- `GET /api/gbp/locations` - 매장 목록
- `GET /api/gbp/reviews` - 리뷰 목록
- `POST /api/gbp/reviews/{review_id}/reply` - 답글 작성

### 리뷰
- `POST /api/reviews/generate-reply` - AI 답글 생성

## 🤖 AI 답글 생성

`data/prompts.json` 파일에서 프롬프트 템플릿을 관리할 수 있습니다:

```json
{
  "default": {
    "positive": "긍정 리뷰용 프롬프트...",
    "neutral": "중립 리뷰용 프롬프트...",
    "negative": "부정 리뷰용 프롬프트..."
  }
}
```

시스템은 리뷰 평점에 따라 자동으로 적절한 프롬프트를 선택합니다:
- 4-5점: positive
- 3점: neutral
- 1-2점: negative

## 🔒 보안 주의사항

- `.env` 파일을 절대 git에 커밋하지 마세요
- OAuth 토큰은 `data/tokens/` 디렉토리에 저장됩니다 (gitignore 처리됨)
- API 키와 시크릿은 안전하게 보관하세요

## 📝 개발 로드맵

### ✅ Stage 1: Google Business Profile (완료)
- [x] Phase 1: 프로젝트 초기 설정
- [x] Phase 2: GBP OAuth 인증
- [x] Phase 3: GBP 리뷰 관리 API
- [x] Phase 4: LLM 답글 생성
- [x] Phase 5: 프론트엔드 UI
- [x] Phase 6: 통합 테스트

### ✅ Stage 2: 네이버 플레이스 (완료)
- [x] Phase 7: Playwright 웹 자동화 기반
- [x] Phase 8: 네이버 리뷰 크롤링 및 답글
- [x] Phase 9: 프론트엔드 네이버 통합
- [x] Phase 10: 전체 시스템 통합

### 🎯 Stage 3: 추가 기능 (선택사항)
- [ ] 카카오맵 프로필 리뷰 관리
- [ ] 알림 시스템 (이메일/슬랙)
- [ ] 리뷰 분석 대시보드
- [ ] Docker 컨테이너화
- [ ] 웹 배포

## 🆘 문제 해결

### 백엔드가 시작되지 않음
- Python 가상환경이 활성화되어 있는지 확인
- `pip install -r requirements.txt`로 의존성 재설치

### OAuth 인증 실패
- `.env` 파일의 `GOOGLE_CLIENT_ID`와 `GOOGLE_CLIENT_SECRET` 확인
- Google Cloud Console에서 리디렉션 URI 확인

### 프론트엔드가 백엔드와 통신하지 못함
- 백엔드 서버가 실행 중인지 확인 (http://localhost:8000)
- CORS 설정 확인

## 📄 라이선스

Private Use Only

## 👥 기여

현재 개인 프로젝트입니다.

