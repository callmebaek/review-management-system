# 🚀 네이버 OAuth 로그인 가이드

## 🎉 혁신적 기능!

EXE 다운로드 없이 **웹에서 바로 로그인**하세요!

### ✅ 장점
- 🚫 EXE 다운로드 불필요
- 🌐 웹에서 즉시 로그인
- ♻️ 브라우저 세션 재사용 (빠름!)
- 🔄 30분 idle 후 자동 정리
- 🔒 OAuth 2.0 표준 보안

---

## 📋 설정 방법

### 1. 네이버 개발자 센터 설정

1. **https://developers.naver.com** 접속
2. **애플리케이션 등록** 또는 기존 앱 선택
3. **"네이버 로그인" API 추가**

#### 필수 입력 사항:

**서비스 URL:**
```
https://review-management-system-ivory.vercel.app
```

**Callback URL:**
```
로컬: http://localhost:8000/api/naver/oauth/callback
프로덕션: https://review-management-system-5bc2651ced45.herokuapp.com/api/naver/oauth/callback
```

→ **둘 다 추가하세요!**

4. **Client ID와 Client Secret 복사**

---

### 2. Heroku 환경 변수 설정

Heroku 대시보드 → Settings → Config Vars:

```
NAVER_CLIENT_ID = NtlZdWIILtT2yOdelsWy
NAVER_CLIENT_SECRET = UDdrU2gK4b
NAVER_OAUTH_CALLBACK_URL = https://review-management-system-5bc2651ced45.herokuapp.com/api/naver/oauth/callback
```

---

### 3. 로컬 개발 환경 설정

`backend/.env` 파일에 추가:

```bash
# 네이버 OAuth
NAVER_CLIENT_ID=NtlZdWIILtT2yOdelsWy
NAVER_CLIENT_SECRET=UDdrU2gK4b
NAVER_OAUTH_CALLBACK_URL=http://localhost:8000/api/naver/oauth/callback
```

---

## 🚀 사용 방법

### 1. **웹앱에서 로그인**

1. 네이버 플레이스 페이지 접속
2. **"네이버로 로그인하기"** 버튼 클릭 (초록색, 맨 위)
3. 네이버 로그인 페이지에서 로그인
4. 2단계 인증 완료
5. "동의하기" 클릭

### 2. **자동 처리**

- ✅ 쿠키 자동 추출
- ✅ 백그라운드 브라우저 등록
- ✅ 즉시 시스템 사용 가능!

### 3. **세션 유지**

- ✅ 사용 중에는 브라우저 유지 (재로그인 불필요)
- ⏱️ 30분 idle 후 자동 종료
- 🔄 다음 사용 시 재로그인 (1분이면 됨)

---

## 🔄 재로그인이 필요한 경우

다음 상황에서 재로그인이 필요합니다:

1. **30분 이상 사용하지 않음**
2. **서버 재시작** (Heroku dyno restart)
3. **명시적 로그아웃**

→ "다시 로그인해주세요" 메시지 표시됨
→ "네이버로 로그인하기" 버튼 다시 클릭

---

## 🎯 작동 원리

```
사용자가 OAuth 로그인
  ↓
서버에 headless 브라우저 생성 & 백그라운드 유지
  ↓
모든 요청에서 이 브라우저 재사용 (쿠키 재로드 불필요!)
  ↓
30분 idle → 자동 정리
```

---

## 📊 EXE 방식과 비교

| 항목 | OAuth 방식 | EXE 방식 |
|------|------------|----------|
| 플랫폼 | 모든 OS | Windows만 |
| 속도 | 1분 | 2-3분 |
| 세션 수명 | 사용 중 무제한 | 몇 시간~며칠 |
| 재로그인 | 웹에서 1분 | EXE 재실행 |
| 다운로드 | 불필요 | 25MB 다운 |

---

## ⚠️ 주의사항

### Heroku 제약:
- Dyno 재시작 시 브라우저 종료
- 24시간마다 재시작 가능
- 배포 시 재시작

→ **정상적인 동작**입니다. 재로그인하면 됩니다!

### 메모리:
- 브라우저 1개 = 약 200-300MB
- Heroku Free: 512MB (충분!)

---

## 🎉 결론

**OAuth 방식이 훨씬 편리합니다!**

- 사용 시작: 웹에서 1분
- 사용 중: 재로그인 불필요
- 다음 사용: 웹에서 1분

EXE는 백업용으로만 유지됩니다.

