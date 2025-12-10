# 🚀 웹 배포 가이드 (비개발자용)

이 가이드는 리뷰 관리 시스템을 웹에 배포하는 **가장 쉬운 방법**을 설명합니다.  
클릭 몇 번으로 완료할 수 있도록 단계별로 안내합니다!

---

## 📋 준비물

- [ ] GitHub 계정 (무료)
- [ ] Railway 계정 (무료 가입, 유료 사용)
- [ ] MongoDB Atlas 계정 (무료)
- [ ] Vercel 계정 (무료)
- [ ] 신용카드 (Railway 유료 플랜용)

**예상 비용:** 월 $5~12 (Railway)  
**설정 시간:** 30분~1시간

---

## 🗂️ Step 1: GitHub에 코드 올리기 (10분)

### 왜 필요한가요?
Railway와 Vercel은 GitHub에서 코드를 가져와서 자동으로 배포합니다.  
코드 수정 후 GitHub에 Push → 자동으로 웹사이트 업데이트!

### 1-1. GitHub 가입 및 Repository 생성

1. **https://github.com 접속 → Sign up**
2. **우측 상단 "+" 버튼 → "New repository"**
3. **설정:**
   - Repository name: `review-management-system`
   - ✅ Public 선택
   - ✅ "Add a README file" 체크
   - **"Create repository"** 버튼 클릭

### 1-2. GitHub Desktop 설치

1. **https://desktop.github.com 접속**
2. **"Download for Windows" 클릭**
3. **설치 후 GitHub 계정으로 로그인**

### 1-3. 코드 업로드

1. **GitHub Desktop 실행**
2. **File → Add Local Repository**
3. **"Choose" 클릭 → 프로젝트 폴더 선택**
   ```
   C:\Users\smbae\OneDrive\Desktop\work automation\review machine
   ```
4. **"Add Repository" 클릭**

5. **만약 에러 나면:**
   - "Create a repository" 선택
   - 같은 폴더 선택
   - "Create Repository" 클릭

6. **업로드:**
   - 좌측에 변경된 파일들 보임
   - 좌측 하단 "Summary" 입력: `Initial commit`
   - **"Commit to main"** 버튼
   - 상단 **"Publish repository"** 버튼
   - **"Publish Repository"** 클릭

**✅ 완료! GitHub에서 본인 계정 → Repositories에서 확인 가능**

---

## 💾 Step 2: MongoDB Atlas 설정 (15분)

### 무료 데이터베이스 만들기

### 2-1. 회원가입

1. **https://www.mongodb.com/cloud/atlas/register 접속**
2. **Google 계정으로 가입 (가장 빠름)**
3. **프로필 정보 입력 → Submit**

### 2-2. 무료 클러스터 생성

1. **"+ Create" 버튼 클릭**
2. **"Shared" 선택 (무료 옵션)**
3. **설정:**
   - Provider: **AWS** 선택
   - Region: **Seoul (ap-northeast-2)** 선택 ⭐ (한국 서버!)
   - Cluster Tier: **M0 Sandbox** 선택 (FREE 표시 확인)
   - Cluster Name: `review-system`
4. **"Create Cluster"** 버튼 (2~3분 소요)

### 2-3. 데이터베이스 사용자 생성

1. **좌측 메뉴 "Database Access" 클릭**
2. **"+ ADD NEW DATABASE USER"** 클릭
3. **설정:**
   - Authentication Method: **Password** 선택
   - Username: `reviewadmin`
   - Password: **"Autogenerate Secure Password"** 클릭
   - 📋 **비밀번호 복사하여 메모장에 저장!** (다시 볼 수 없습니다)
   - Database User Privileges: **Atlas admin** 선택
4. **"Add User"** 버튼

### 2-4. 네트워크 접근 허용

1. **좌측 메뉴 "Network Access" 클릭**
2. **"+ ADD IP ADDRESS"** 클릭
3. **"ALLOW ACCESS FROM ANYWHERE"** 클릭 ✅
   - IP: `0.0.0.0/0` 자동 입력됨
4. **"Confirm"** 버튼

### 2-5. 연결 문자열 가져오기

1. **좌측 메뉴 "Database" 클릭**
2. **클러스터 옆 "Connect" 버튼 클릭**
3. **"Drivers" 선택**
4. **Driver: Python / Version: 3.12 or later 선택**
5. **연결 문자열 복사:**
   ```
   mongodb+srv://reviewadmin:<password>@review-system.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. **`<password>` 부분을 2-3에서 복사한 실제 비밀번호로 변경:**
   ```
   mongodb+srv://reviewadmin:실제비밀번호@review-system.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
7. **📋 메모장에 저장!**

**✅ MongoDB 준비 완료!**

---

## 🚂 Step 3: Railway로 백엔드 배포 (20분)

### 3-1. 가입 및 프로젝트 생성

1. **https://railway.app 접속**
2. **"Start a New Project" 클릭**
3. **"Login with GitHub" 선택**
4. **GitHub 인증 → Authorize Railway**

### 3-2. 프로젝트 배포

1. **"Deploy from GitHub repo" 선택**
2. **"Configure GitHub App" 클릭**
3. **Repository access 설정:**
   - "Only select repositories" 선택
   - `review-management-system` 선택
   - **"Save"** 클릭
4. **`review-management-system` 저장소 선택**
5. **"Deploy Now" 클릭**

⚠️ **배포가 시작되지만 환경 변수가 없어서 실패할 수 있습니다. 다음 단계로 진행하세요!**

### 3-3. 환경 변수 설정

1. **Railway Dashboard → 배포된 프로젝트 클릭**
2. **"Variables" 탭 클릭**
3. **"New Variable" 버튼 클릭하여 하나씩 추가:**

```bash
# MongoDB (Step 2-5에서 복사한 연결 문자열)
MONGODB_URL=mongodb+srv://reviewadmin:실제비밀번호@review-system.xxxxx.mongodb.net/?retryWrites=true&w=majority

# MongoDB 사용 활성화
USE_MONGODB=true

# Google OAuth (Google Cloud Console에서 발급받은 것)
GOOGLE_CLIENT_ID=당신의_구글_클라이언트_ID
GOOGLE_CLIENT_SECRET=당신의_구글_시크릿
GOOGLE_REDIRECT_URI=https://your-app.up.railway.app/auth/google/callback

# OpenAI
OPENAI_API_KEY=sk-당신의_OpenAI_키
OPENAI_MODEL=gpt-4o-mini

# Server
BACKEND_PORT=8000

# Mock 설정 (프로덕션에서는 모두 false)
USE_MOCK_GBP=false
USE_MOCK_NAVER=false
```

4. **모든 변수 입력 후 자동 재배포됨**

### 3-4. 도메인 생성

1. **"Settings" 탭 클릭**
2. **"Domains" 섹션에서 "Generate Domain" 클릭**
3. **생성된 URL 복사:**
   ```
   https://review-management-system-production-xxxx.up.railway.app
   ```
4. **📋 메모장에 저장!**

### 3-5. Google OAuth 콜백 URL 업데이트

1. **Google Cloud Console (https://console.cloud.google.com) 접속**
2. **본인 프로젝트 선택**
3. **"API 및 서비스" → "사용자 인증 정보"**
4. **OAuth 2.0 클라이언트 ID 클릭**
5. **"승인된 리디렉션 URI" 섹션에 추가:**
   ```
   https://review-management-system-production-xxxx.up.railway.app/auth/google/callback
   ```
6. **"저장" 클릭**

7. **Railway로 돌아가서 환경 변수 업데이트:**
   ```
   GOOGLE_REDIRECT_URI=https://review-management-system-production-xxxx.up.railway.app/auth/google/callback
   ```

**✅ 백엔드 배포 완료!**

---

## 🎨 Step 4: Vercel로 프론트엔드 배포 (10분)

### 4-1. 가입 및 프로젝트 생성

1. **https://vercel.com 접속**
2. **"Sign Up" → GitHub 계정 연결**
3. **Authorize Vercel**

### 4-2. 프로젝트 Import

1. **"Add New..." → "Project" 클릭**
2. **"Import Git Repository" 섹션에서:**
   - `review-management-system` 선택
   - **"Import"** 클릭

### 4-3. 빌드 설정

**Configure Project 화면에서:**

1. **Framework Preset:** Vite (자동 감지됨)
2. **Root Directory:** `frontend` ⬅️ **중요! Edit 클릭 후 변경**
3. **Build Command:** `npm run build` (기본값)
4. **Output Directory:** `dist` (기본값)

### 4-4. 환경 변수 추가

**Environment Variables 섹션에서:**

```bash
Name: VITE_API_URL
Value: https://review-management-system-production-xxxx.up.railway.app
```

**⚠️ Railway에서 생성한 백엔드 URL을 입력하세요!**

5. **"Deploy" 버튼 클릭**

### 4-5. 배포 완료 확인

1. **배포 완료 후 "Visit" 버튼 클릭**
2. **생성된 URL:**
   ```
   https://review-management-system.vercel.app
   ```
3. **📋 이 URL이 당신의 웹사이트 주소입니다!**

**✅ 프론트엔드 배포 완료!**

---

## 🧪 Step 5: 테스트하기

### 5-1. 웹사이트 접속

1. **Vercel URL 접속:**
   ```
   https://review-management-system.vercel.app
   ```

### 5-2. Google 로그인 테스트

1. **"Google 계정으로 로그인" 버튼 클릭**
2. **Google 계정 선택**
3. **권한 요청 화면에서 "허용" 클릭**
4. **대시보드로 리디렉션 확인**

### 5-3. 기능 테스트

1. **Google 리뷰 조회**
2. **AI 답글 생성**
3. **답글 게시**

---

## 🔧 네이버 기능 설정 (선택사항)

### 네이버는 로컬 인증 필요!

클라우드에서 네이버 자동 로그인이 어렵기 때문에, 로컬에서 한 번 로그인한 후 세션을 업로드하는 방식을 사용합니다.

### 방법 1: 로컬에서 세션 생성

1. **로컬 컴퓨터에서 리뷰 시스템 실행**
   ```bash
   cd backend
   python main.py
   ```

2. **http://localhost:8000 접속**

3. **네이버 로그인 수행 (headless=False)**
   - 브라우저가 뜨면 직접 로그인
   - 캡차/2단계 인증 처리

4. **로그인 성공 후 세션 파일 생성됨:**
   ```
   data/naver_sessions/session.json
   ```

### 방법 2: 세션을 클라우드로 업로드

**향후 업데이트에서 추가될 기능:**
- 로컬에서 생성한 세션을 웹 UI로 업로드
- 클라우드는 업로드된 세션 사용

---

## 💰 비용 정리

| 서비스 | 플랜 | 비용 |
|--------|------|------|
| **MongoDB Atlas** | M0 Free Tier | **무료** (512MB) |
| **Railway** | Hobby Plan | **$5/월** |
| **Vercel** | Hobby (개인용) | **무료** |
| **도메인** (선택) | .com | $10/년 |

**총 비용: 월 $5 = 연간 $60**

---

## 🔄 코드 업데이트 방법

코드를 수정한 후 배포하는 방법:

### 1. 로컬에서 코드 수정
VS Code나 원하는 에디터로 코드 수정

### 2. GitHub Desktop에서 커밋

1. **GitHub Desktop 실행**
2. **변경된 파일들 확인**
3. **Summary 입력:** "리뷰 기능 개선"
4. **"Commit to main"** 버튼
5. **"Push origin"** 버튼

### 3. 자동 배포

- Railway: GitHub Push 감지 → 자동 재배포 (2~5분)
- Vercel: GitHub Push 감지 → 자동 재배포 (1~2분)

**끝! 5분 후 웹사이트에 변경사항 반영됩니다.**

---

## 🆘 문제 해결

### Railway 배포 실패

1. **"Deployments" 탭에서 로그 확인**
2. **일반적인 원인:**
   - 환경 변수 누락
   - MongoDB 연결 실패
   - Playwright 설치 실패

**해결책:**
- 환경 변수 다시 확인
- MongoDB URL 정확한지 확인
- Railway 재배포 시도

### Vercel 배포 실패

1. **"Deployments" 탭에서 로그 확인**
2. **일반적인 원인:**
   - Root Directory가 `frontend`로 설정되지 않음
   - 환경 변수 누락

**해결책:**
- Project Settings → Root Directory 확인
- Environment Variables 재확인

### CORS 에러

**증상:** 프론트엔드에서 백엔드 호출 시 에러

**해결책:**
1. **백엔드 `main.py` 확인:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://review-management-system.vercel.app"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
2. **Vercel URL을 allow_origins에 추가**
3. **GitHub에 커밋 → 자동 재배포**

---

## ✅ 체크리스트

배포 완료 확인:

- [ ] GitHub에 코드 업로드 완료
- [ ] MongoDB Atlas 클러스터 생성
- [ ] MongoDB 연결 문자열 획득
- [ ] Railway 백엔드 배포 완료
- [ ] Railway 환경 변수 설정
- [ ] Railway 도메인 생성
- [ ] Google OAuth 콜백 URL 추가
- [ ] Vercel 프론트엔드 배포 완료
- [ ] Vercel 환경 변수 설정
- [ ] 웹사이트 접속 가능
- [ ] Google 로그인 성공
- [ ] 리뷰 조회 성공
- [ ] AI 답글 생성 성공

**모든 항목 체크 완료 시 배포 성공! 🎉**

---

## 📞 추가 도움이 필요하면?

- Railway 문서: https://docs.railway.app
- Vercel 문서: https://vercel.com/docs
- MongoDB Atlas 문서: https://docs.atlas.mongodb.com

---

**축하합니다! 리뷰 관리 시스템이 웹에서 작동합니다! 🚀**

