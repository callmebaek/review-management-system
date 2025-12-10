# ⚡ 빠른 시작 가이드 (5분 요약)

웹 배포를 위한 핵심 단계만 정리했습니다.

---

## ✅ 체크리스트

### 1단계: 코드 준비 완료 ✅

다음 파일들이 자동으로 생성되었습니다:

- ✅ `railway.json` - Railway 배포 설정
- ✅ `Procfile` - 실행 명령어
- ✅ `nixpacks.toml` - 빌드 설정
- ✅ `backend/utils/db.py` - MongoDB 연동 코드
- ✅ `backend/requirements.txt` - pymongo 추가됨
- ✅ `env.example` - 환경 변수 템플릿
- ✅ `frontend/vercel.json` - Vercel 설정
- ✅ `DEPLOYMENT_GUIDE.md` - 상세 배포 가이드

**이제 GitHub에 올리기만 하면 됩니다!**

---

## 📤 2단계: GitHub에 올리기 (5분)

### 방법 A: GitHub Desktop (추천)

1. **GitHub Desktop 설치:** https://desktop.github.com
2. **File → Add Local Repository**
3. **이 폴더 선택:** 
   ```
   C:\Users\smbae\OneDrive\Desktop\work automation\review machine
   ```
4. **Commit to main** 입력: `웹 배포 준비 완료`
5. **Publish repository** 클릭
6. **Repository name:** `review-management-system`

### 방법 B: 명령줄

```bash
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine"
git init
git add .
git commit -m "웹 배포 준비 완료"
git branch -M main
git remote add origin https://github.com/당신의아이디/review-management-system
git push -u origin main
```

---

## 💾 3단계: MongoDB 설정 (10분)

1. **https://mongodb.com/cloud/atlas/register** 가입
2. **무료 클러스터 생성:**
   - Provider: AWS
   - Region: Seoul (ap-northeast-2)
   - Tier: M0 (FREE)
3. **사용자 생성:**
   - Username: `reviewadmin`
   - Password: 자동 생성 후 **복사!**
4. **Network Access:** "Allow from Anywhere"
5. **연결 문자열 복사:**
   ```
   mongodb+srv://reviewadmin:비밀번호@cluster.mongodb.net/
   ```

---

## 🚂 4단계: Railway 배포 (10분)

1. **https://railway.app** 가입 (GitHub 연결)
2. **New Project → Deploy from GitHub repo**
3. **`review-management-system` 선택**
4. **Variables 탭에서 환경 변수 추가:**

```bash
MONGODB_URL=mongodb+srv://reviewadmin:비밀번호@cluster.mongodb.net/
USE_MONGODB=true
GOOGLE_CLIENT_ID=당신의_구글_클라이언트_ID
GOOGLE_CLIENT_SECRET=당신의_구글_시크릿
OPENAI_API_KEY=sk-당신의_OpenAI_키
BACKEND_PORT=8000
```

5. **Settings → Generate Domain**
6. **생성된 URL 복사** (예: https://xxx.up.railway.app)

---

## 🎨 5단계: Vercel 배포 (5분)

1. **https://vercel.com** 가입 (GitHub 연결)
2. **New Project → Import `review-management-system`**
3. **설정:**
   - Root Directory: **frontend** (중요!)
   - Framework: Vite (자동 감지)
4. **Environment Variables:**
   ```
   VITE_API_BASE_URL=https://xxx.up.railway.app
   ```
   (Railway에서 복사한 URL)
5. **Deploy 클릭**

---

## 🔑 6단계: Google OAuth 업데이트 (5분)

1. **Google Cloud Console** 접속
2. **OAuth 클라이언트 ID → 승인된 리디렉션 URI 추가:**
   ```
   https://xxx.up.railway.app/auth/google/callback
   ```
3. **저장**

4. **Railway로 돌아가서 환경 변수 추가:**
   ```
   GOOGLE_REDIRECT_URI=https://xxx.up.railway.app/auth/google/callback
   FRONTEND_URL=https://xxx.vercel.app
   ```

---

## ✅ 완료!

**웹사이트 접속:** https://xxx.vercel.app

**테스트:**
1. Google 로그인
2. 리뷰 조회
3. AI 답글 생성

---

## 🔧 문제가 있나요?

**Railway 배포 실패:**
- Deployments 탭 → 로그 확인
- 환경 변수 누락 여부 확인

**Vercel 배포 실패:**
- Root Directory가 `frontend`인지 확인

**CORS 에러:**
- Railway Variables에 `FRONTEND_URL` 추가했는지 확인

---

## 📚 더 자세한 가이드

- **DEPLOYMENT_GUIDE.md** - 스크린샷과 함께 상세 설명
- **README.md** - 로컬 개발 가이드

---

**배포 비용:** 월 $5 (Railway) + 무료 (MongoDB, Vercel)

**축하합니다! 🎉**

