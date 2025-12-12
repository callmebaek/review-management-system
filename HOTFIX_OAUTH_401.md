# 🔥 핫픽스: Google OAuth 401 에러 해결

## 🐛 발견된 버그

### 에러 메시지
```
❌ Failed to get Google user info: <HttpError 401 when requesting 
https://www.googleapis.com/oauth2/v2/userinfo?alt=json returned 
"Request is missing required authentication credential. 
Expected OAuth 2 access token, login cookie or other valid authentication credential."
```

### 증상
- 사용자가 구글 로그인 시도
- 구글 인증은 성공하지만 사용자 정보 가져오기 실패
- "Google 계정 정보를 가져올 수 없습니다" 에러 표시
- 로그인 불가

### 근본 원인

1. **OAuth 스코프 누락**
   ```python
   # ❌ Before: userinfo 스코프 없음
   SCOPES = [
       'https://www.googleapis.com/auth/business.manage',
   ]
   ```

2. **API 호출 방식 문제**
   ```python
   # ❌ Before: googleapiclient.discovery 사용
   service = build('oauth2', 'v2', credentials=credentials)
   user_info = service.userinfo().get().execute()
   # → credentials 객체가 제대로 전달되지 않음
   ```

## ✅ 해결 방법

### 1. OAuth 스코프 추가

**파일:** `backend/api/routes/auth.py`

```python
# ✅ After: userinfo 스코프 추가
SCOPES = [
    'https://www.googleapis.com/auth/business.manage',
    'https://www.googleapis.com/auth/userinfo.email',    # 🔐 이메일 정보
    'https://www.googleapis.com/auth/userinfo.profile',  # 🔐 프로필 정보
    'openid',                                            # 🔐 OpenID Connect
]
```

**효과:**
- ✅ Google OAuth에서 이메일 및 프로필 정보 접근 권한 요청
- ✅ access token에 userinfo 스코프 포함

### 2. API 호출 방식 변경

**변경 전:**
```python
# ❌ googleapiclient.discovery 사용 (복잡, 불안정)
from googleapiclient.discovery import build

service = build('oauth2', 'v2', credentials=credentials)
user_info = service.userinfo().get().execute()
```

**변경 후:**
```python
# ✅ requests로 직접 호출 (간단, 안정적)
import requests

headers = {
    'Authorization': f'Bearer {credentials.token}'
}
response = requests.get(
    'https://www.googleapis.com/oauth2/v2/userinfo',
    headers=headers,
    timeout=10
)

user_info = response.json()
user_email = user_info.get('email')
user_name = user_info.get('name')
```

**장점:**
- ✅ 직접 access token 사용 → 인증 문제 없음
- ✅ 간단하고 명확한 코드
- ✅ 타임아웃 설정 가능
- ✅ 에러 처리 용이

### 3. 의존성 추가

**파일:** `backend/requirements.txt`

```python
# 추가
requests==2.31.0  # 🔐 Google API 직접 호출용
```

## 🔍 변경 사항 요약

### 수정된 파일
1. ✅ `backend/api/routes/auth.py`
   - OAuth 스코프 추가 (userinfo.email, userinfo.profile, openid)
   - Google API 호출 방식 변경 (discovery → requests)
   - 에러 처리 강화 (traceback 추가)

2. ✅ `backend/requirements.txt`
   - `requests==2.31.0` 추가

### 코드 변경 라인
```python
# Line 13-18: OAuth 스코프 추가
SCOPES = [
    'https://www.googleapis.com/auth/business.manage',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
]

# Line 7: import 추가
import requests

# Line 89-115: API 호출 방식 변경
try:
    headers = {
        'Authorization': f'Bearer {credentials.token}'
    }
    response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers=headers,
        timeout=10
    )
    
    if response.status_code != 200:
        raise Exception(f"Google API returned {response.status_code}: {response.text}")
    
    user_info = response.json()
    user_email = user_info.get('email', None)
    user_name = user_info.get('name', '')
    
    if not user_email:
        raise Exception("Failed to get email from Google")
    
    print(f"✅ Google user logged in: {user_email} ({user_name})")
    
except Exception as e:
    print(f"❌ Failed to get Google user info: {e}")
    import traceback
    traceback.print_exc()
    
    frontend_url = os.getenv("FRONTEND_URL", f"http://localhost:{settings.frontend_port}")
    return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed")
```

## 🧪 테스트 시나리오

### 테스트 1: 정상 로그인
```
1. 로그인 페이지 접속
2. "로그인" 버튼 클릭
3. Google 계정 선택
4. 권한 요청 화면에서:
   - "리뷰 관리 시스템이 다음을 요청합니다:"
   - ✅ 이메일 주소 확인
   - ✅ 기본 프로필 정보 확인
   - ✅ Google Business Profile 액세스
5. "허용" 클릭
6. Dashboard로 리디렉션
```

**예상 결과:**
- ✅ 로그인 성공
- ✅ Dashboard에 이메일 표시
- ✅ 백엔드 로그: "✅ Google user logged in: user@gmail.com (User Name)"

### 테스트 2: 기존 사용자 (이미 권한 부여)
```
1. 로그인 페이지 접속
2. "로그인" 버튼 클릭
3. Google 계정 선택
4. 자동으로 Dashboard로 이동 (권한 재요청 없음)
```

**예상 결과:**
- ✅ 빠른 로그인 (권한 화면 생략)
- ✅ Dashboard 정상 표시

### 테스트 3: 권한 거부
```
1. 로그인 페이지 접속
2. "로그인" 버튼 클릭
3. Google 계정 선택
4. "취소" 클릭
```

**예상 결과:**
- ✅ 로그인 페이지로 돌아감
- ✅ 에러 메시지 표시

## 🚀 배포 순서

### 1단계: 로컬 테스트 (선택사항)

```bash
cd "c:\Users\smbae\OneDrive\Desktop\work automation\review-management-system\backend"

# 의존성 설치
pip install requests==2.31.0

# 로컬 서버 실행
uvicorn main:app --reload --port 8000

# 테스트
# http://localhost:8000 접속하여 로그인 테스트
```

### 2단계: GitHub 푸시

```bash
cd "c:\Users\smbae\OneDrive\Desktop\work automation\review-management-system"

git add .

git commit -m "fix: Google OAuth 401 에러 해결

- OAuth 스코프에 userinfo.email, userinfo.profile, openid 추가
- Google API 호출 방식 변경 (discovery → requests)
- 직접 access token 사용으로 인증 문제 해결
- 에러 처리 및 로깅 강화
- requests 의존성 추가"

git push origin main
```

### 3단계: Heroku 배포

```bash
cd backend

# Heroku에 배포
git push heroku main

# 배포 로그 확인
heroku logs --tail

# 예상 로그:
# "Building source:"
# "Installing requirements..."
# "Successfully installed requests-2.31.0"
# "Starting gunicorn..."
```

### 4단계: 배포 확인

```bash
# 헬스 체크
curl https://review-management-system-5bc2651ced45.herokuapp.com/health

# 응답: {"status": "healthy"}
```

### 5단계: 실제 테스트

1. **프론트엔드 접속**
   - https://review-management-system-ivory.vercel.app

2. **로그인 테스트**
   - 로그인 버튼 클릭
   - Google 계정 선택
   - 권한 허용
   - Dashboard 확인

3. **백엔드 로그 확인**
   ```bash
   heroku logs --tail
   
   # 예상 로그:
   # "✅ Google user logged in: user@gmail.com (User Name)"
   ```

## 📊 수정 전후 비교

### Before (401 에러)
```
1. 사용자 로그인 시도
2. Google OAuth 성공
3. credentials 획득
4. discovery API로 userinfo 요청
   ❌ 401 Error: Missing authentication credential
5. 로그인 실패
6. 에러 메시지 표시
```

### After (정상 작동)
```
1. 사용자 로그인 시도
2. Google OAuth 성공 (userinfo 스코프 포함)
3. credentials 획득 (access token 포함)
4. requests로 직접 userinfo 요청
   ✅ Authorization: Bearer {access_token}
   ✅ 200 OK: {"email": "...", "name": "..."}
5. 로그인 성공
6. Dashboard 표시
```

## 🔍 기술적 세부사항

### OAuth 2.0 스코프 설명

1. **`https://www.googleapis.com/auth/business.manage`**
   - Google Business Profile 관리 권한
   - 매장 정보, 리뷰 조회 및 답글 작성

2. **`https://www.googleapis.com/auth/userinfo.email`** 🆕
   - 사용자 이메일 주소 조회
   - 필수: 세션 관리 및 권한 검증

3. **`https://www.googleapis.com/auth/userinfo.profile`** 🆕
   - 사용자 이름, 프로필 사진 등
   - 선택: UI에 사용자 정보 표시

4. **`openid`** 🆕
   - OpenID Connect 프로토콜
   - 표준 인증 정보 제공

### Google UserInfo API

**Endpoint:**
```
GET https://www.googleapis.com/oauth2/v2/userinfo
```

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": "1234567890",
  "email": "user@gmail.com",
  "verified_email": true,
  "name": "John Doe",
  "given_name": "John",
  "family_name": "Doe",
  "picture": "https://..."
}
```

### 왜 requests가 더 나은가?

| 비교 | googleapiclient.discovery | requests |
|------|---------------------------|----------|
| 복잡도 | 높음 (3단계) | 낮음 (1단계) |
| 의존성 | 무거움 (여러 패키지) | 가벼움 (1개) |
| 디버깅 | 어려움 (내부 구조 복잡) | 쉬움 (HTTP 요청 그대로) |
| 에러 처리 | HttpError 객체 (복잡) | 간단한 status_code 확인 |
| 성능 | 느림 (객체 생성 오버헤드) | 빠름 (직접 요청) |

## ⚠️ 주의사항

### 1. 사용자 재인증 필요

이번 수정으로 OAuth 스코프가 변경되었으므로:
- ✅ **신규 사용자**: 자동으로 새 스코프 요청
- ⚠️ **기존 사용자**: 로그아웃 후 다시 로그인 필요

**기존 사용자 안내:**
```
배포 후 기존 사용자에게 공지:
"시스템 업데이트로 인해 다시 로그인해주세요."
```

### 2. Google Cloud Console 설정 확인

OAuth 2.0 동의 화면에서 새 스코프가 추가되었는지 확인:
1. Google Cloud Console 접속
2. "APIs & Services" → "OAuth 동의 화면"
3. 스코프 확인:
   - ✅ userinfo.email
   - ✅ userinfo.profile
   - ✅ openid

### 3. 모니터링

배포 후 24시간 동안 로그 모니터링:
```bash
heroku logs --tail | grep "Google user logged in"

# 예상 로그:
# "✅ Google user logged in: user1@gmail.com (User 1)"
# "✅ Google user logged in: user2@gmail.com (User 2)"
```

## 🎉 예상 효과

### 사용자 경험
- ✅ 로그인 성공률 100%
- ✅ 명확한 권한 요청 화면
- ✅ 빠른 로그인 프로세스

### 시스템 안정성
- ✅ 401 에러 제거
- ✅ 안정적인 사용자 정보 조회
- ✅ 명확한 에러 처리

### 보안
- ✅ 표준 OAuth 2.0 스코프 사용
- ✅ 최소 권한 원칙 준수
- ✅ 투명한 권한 요청

---

**작성일:** 2024-12-12
**담당자:** AI Assistant
**우선순위:** 🔥 Critical (로그인 불가)
**상태:** ✅ 수정 완료, 배포 대기


