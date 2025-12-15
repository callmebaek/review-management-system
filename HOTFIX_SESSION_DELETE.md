# 🔥 핫픽스: 세션 삭제 로직 개선 (다중 사용자 지원)

## 🐛 발견된 버그

### 문제 상황
```
1. 구글 계정 A, B가 네이버 세션을 공유
   → google_emails: ["A@gmail.com", "B@gmail.com"]

2. 계정 A로 로그인해서 "세션 삭제" 클릭
   → 세션 전체가 삭제됨 (db.delete_one 실행) ❌

3. 결과: 계정 B도 세션 사용 불가 ❌
```

### 근본 원인
```python
# ❌ Before: 세션 전체 삭제
result = db.naver_sessions.delete_one({"_id": user_id})
```

## ✅ 해결 방법

### 기대 동작
```
1. 구글 계정 A, B가 네이버 세션을 공유
   → google_emails: ["A@gmail.com", "B@gmail.com"]

2. 계정 A로 로그인해서 "세션 삭제" 클릭
   → google_emails에서 A만 제거
   → google_emails: ["B@gmail.com"] ✅
   → 메시지: "다른 사용자 1명은 계속 사용 가능"

3. 결과: 계정 B는 계속 세션 사용 가능 ✅

4. 계정 B도 "세션 삭제" 클릭
   → google_emails: []
   → 배열이 비었으므로 세션 전체 삭제 ✅
   → 메시지: "세션이 완전히 삭제되었습니다"
```

## 🔧 구현 내용

### 1. 백엔드: 스마트 세션 삭제 로직

**파일:** `backend/api/routes/naver.py`

**새로운 로직:**
```python
@router.delete("/session")
async def delete_session(user_id, google_email):
    """
    📝 동작:
      1. google_emails 배열에서 현재 사용자의 이메일만 제거
      2. 배열이 비면 세션 전체 삭제
      3. 다른 사용자는 계속 세션 사용 가능
    """
    # 현재 세션 조회
    session = db.naver_sessions.find_one({"_id": user_id})
    google_emails = session.get("google_emails", [])
    
    # 현재 사용자의 이메일만 제거
    if google_email in google_emails:
        google_emails.remove(google_email)
    
    # 배열이 비었으면 세션 전체 삭제, 아니면 업데이트
    if len(google_emails) == 0:
        # 마지막 사용자 → 세션 전체 삭제
        db.naver_sessions.delete_one({"_id": user_id})
        return {
            "success": True,
            "action": "deleted",  # 🆕
            "remaining_users": 0
        }
    else:
        # 다른 사용자 있음 → google_emails만 업데이트
        db.naver_sessions.update_one(
            {"_id": user_id},
            {"$set": {"google_emails": google_emails}}
        )
        return {
            "success": True,
            "action": "disconnected",  # 🆕
            "remaining_users": len(google_emails)
        }
```

**응답 형식:**

**케이스 1: 본인만 연결 해제 (다른 사용자 있음)**
```json
{
  "success": true,
  "message": "세션 연결이 해제되었습니다 (다른 사용자 2명은 계속 사용 가능)",
  "action": "disconnected",
  "remaining_users": 2
}
```

**케이스 2: 세션 완전 삭제 (마지막 사용자)**
```json
{
  "success": true,
  "message": "세션이 완전히 삭제되었습니다",
  "action": "deleted",
  "remaining_users": 0
}
```

### 2. 프론트엔드: 사용자 친화적 메시지

**파일:** `frontend/src/pages/NaverLogin.jsx`

**개선 사항:**

1. **삭제 확인 다이얼로그 개선**
```javascript
const googleEmail = localStorage.getItem('google_email')
const googleName = localStorage.getItem('google_name')

confirm(
  `'${user_id}' 세션에서 연결을 해제하시겠습니까?\n\n` +
  `현재 계정: ${googleName}\n` +
  `- 다른 사용자가 이 세션을 공유 중이면 본인만 연결 해제됩니다.\n` +
  `- 본인만 사용 중이면 세션이 완전히 삭제됩니다.`
)
```

2. **응답에 따른 다른 메시지**
```javascript
if (response.data.action === 'deleted') {
  // 세션 완전 삭제됨
  alert(`✅ 세션이 완전히 삭제되었습니다.\n다시 사용하려면 EXE로 세션을 재생성하세요.`)
} else if (response.data.action === 'disconnected') {
  // 본인만 연결 해제됨
  alert(
    `✅ 연결이 해제되었습니다.\n\n` +
    `다른 사용자 ${response.data.remaining_users}명은 계속 이 세션을 사용할 수 있습니다.`
  )
}
```

## 🎯 사용 시나리오

### 시나리오 1: 개인 사용 (1명만 사용)

```
📝 상황:
- 구글 계정 A만 네이버 세션 사용
- google_emails: ["A@gmail.com"]

🗑️ 계정 A가 세션 삭제:
1. 확인 다이얼로그 표시
2. 승인 → google_emails에서 A 제거
3. 배열이 비었으므로 세션 전체 삭제
4. 메시지: "✅ 세션이 완전히 삭제되었습니다"

✅ 결과:
- 세션 완전히 제거
- 다시 사용하려면 EXE로 재생성 필요
```

### 시나리오 2: 팀 사용 (여러 명 공유)

```
📝 상황:
- 구글 계정 A, B, C가 네이버 세션 공유
- google_emails: ["A@gmail.com", "B@gmail.com", "C@gmail.com"]

🗑️ 계정 A가 세션 삭제:
1. 확인 다이얼로그 표시
   "다른 사용자가 이 세션을 공유 중이면 본인만 연결 해제됩니다"
2. 승인 → google_emails에서 A만 제거
3. 업데이트: ["B@gmail.com", "C@gmail.com"]
4. 메시지: "✅ 연결이 해제되었습니다. 다른 사용자 2명은 계속 사용 가능"

✅ 결과:
- 계정 A: 세션 사용 불가
- 계정 B, C: 계속 세션 사용 가능 ✅

🗑️ 계정 B가 세션 삭제:
1. google_emails에서 B 제거
2. 업데이트: ["C@gmail.com"]
3. 메시지: "✅ 연결이 해제되었습니다. 다른 사용자 1명은 계속 사용 가능"

✅ 결과:
- 계정 A, B: 세션 사용 불가
- 계정 C: 계속 세션 사용 가능 ✅

🗑️ 계정 C가 세션 삭제:
1. google_emails에서 C 제거
2. 배열이 비었으므로 세션 전체 삭제
3. 메시지: "✅ 세션이 완전히 삭제되었습니다"

✅ 결과:
- 세션 완전히 제거
- 모든 계정이 사용 불가
```

### 시나리오 3: 퇴사자 처리

```
📝 상황:
- 회사 네이버 세션을 직원 A, B, C가 공유
- 직원 A가 퇴사

🗑️ 방법 1: 퇴사자가 직접 삭제
1. 계정 A로 로그인
2. "세션 삭제" 클릭
3. A만 google_emails에서 제거

✅ 결과:
- 직원 B, C는 계속 사용 가능
- 직원 A는 접근 불가 (권한 검증으로 차단)

🗑️ 방법 2: 관리자가 MongoDB에서 직접 제거
```javascript
// MongoDB에서 직접 수정
db.naver_sessions.updateOne(
  { _id: "company_naver" },
  { $pull: { google_emails: "퇴사자@company.com" } }
)
```
```

## 🧪 테스트 시나리오

### 테스트 1: 개인 사용자 세션 삭제

```
1. 구글 계정 A로 로그인
2. EXE로 네이버 세션 생성 (Google: A만)
3. 네이버 로그인 페이지에서 "삭제" 클릭
4. 확인 메시지 확인
5. 승인

예상 결과:
✅ "세션이 완전히 삭제되었습니다" 메시지
✅ 세션 목록에서 제거
✅ Dashboard에서 "연결되지 않음" 표시
```

### 테스트 2: 다중 사용자 세션 부분 삭제

```
1. EXE로 네이버 세션 생성 (Google: A, B 입력)
2. 계정 A로 로그인 → "삭제" 클릭

예상 결과:
✅ "다른 사용자 1명은 계속 사용 가능" 메시지
✅ 계정 A: 세션 목록에서 제거
✅ 계정 B로 로그인 → 세션 여전히 존재 ✅

3. 계정 B로 로그인 → "삭제" 클릭

예상 결과:
✅ "세션이 완전히 삭제되었습니다" 메시지
✅ 세션 완전히 제거
```

### 테스트 3: 권한 검증

```
1. EXE로 네이버 세션 생성 (Google: A만)
2. 계정 B로 로그인
3. 매장 목록 조회 시도

예상 결과:
✅ 403 에러 (권한 없음)
✅ 계정 B는 세션 목록에서 해당 세션을 볼 수 없음

4. 계정 A로 로그인해서 삭제 시도

예상 결과:
✅ 권한 검증 통과
✅ 세션 삭제 성공
```

## 📊 수정 전후 비교

### Before (버그)

| 동작 | 결과 |
|------|------|
| 계정 A, B가 세션 공유 | ✅ 가능 |
| 계정 A가 세션 삭제 | ❌ 세션 전체 삭제 |
| 계정 B의 접근 | ❌ 불가능 (세션 없음) |

### After (수정)

| 동작 | 결과 |
|------|------|
| 계정 A, B가 세션 공유 | ✅ 가능 |
| 계정 A가 세션 삭제 | ✅ A만 연결 해제 |
| 계정 B의 접근 | ✅ 계속 가능 |
| 계정 B도 세션 삭제 | ✅ 세션 완전 삭제 |

## 🚀 배포 가이드

### 1단계: GitHub 푸시

```bash
cd "c:\Users\smbae\OneDrive\Desktop\work automation\review-management-system"

git add .

git commit -m "fix: 다중 사용자 세션 삭제 로직 개선

- google_emails 배열에서 현재 사용자만 제거
- 마지막 사용자가 삭제할 때만 세션 완전 삭제
- 프론트엔드에 명확한 메시지 표시 (deleted vs disconnected)
- 팀 단위 세션 공유 시 다른 사용자에게 영향 없음

Fixes: 세션 삭제 시 다른 사용자도 삭제되는 버그"

git push origin main
```

### 2단계: Heroku 배포 (백엔드)

```bash
cd backend
git push heroku main
heroku logs --tail
```

### 3단계: Vercel 배포 (프론트엔드)

```bash
cd ../frontend
vercel --prod
```

### 4단계: 배포 확인

```bash
# 헬스 체크
curl https://review-management-system-5bc2651ced45.herokuapp.com/health

# 프론트엔드 접속
open https://review-management-system-ivory.vercel.app
```

### 5단계: 실제 테스트

1. **테스트 준비**
   - 구글 계정 2개 준비 (또는 테스트용 계정)
   - EXE로 네이버 세션 생성 시 두 계정 모두 입력

2. **삭제 테스트**
   - 계정 1로 로그인 → 세션 삭제
   - 메시지 확인: "다른 사용자 1명은 계속 사용 가능"
   - 계정 2로 로그인 → 세션 여전히 존재하는지 확인

3. **완전 삭제 테스트**
   - 계정 2로도 세션 삭제
   - 메시지 확인: "세션이 완전히 삭제되었습니다"

## 🔍 기술적 세부사항

### MongoDB 연산

**Before:**
```javascript
// ❌ 전체 세션 삭제
db.naver_sessions.delete_one({"_id": user_id})
```

**After:**
```javascript
// ✅ 스마트 삭제
// 1. 배열에서 이메일 제거
google_emails.remove(google_email)

// 2. 조건부 삭제/업데이트
if len(google_emails) == 0:
    # 완전 삭제
    db.naver_sessions.delete_one({"_id": user_id})
else:
    # 배열만 업데이트
    db.naver_sessions.update_one(
        {"_id": user_id},
        {"$set": {"google_emails": google_emails}}
    )
```

### 대안: MongoDB $pull 연산자 사용

더 간결한 방법 (향후 리팩토링 시 고려):
```python
# 배열에서 직접 제거
db.naver_sessions.update_one(
    {"_id": user_id},
    {"$pull": {"google_emails": google_email}}
)

# 빈 배열 확인 후 삭제
session = db.naver_sessions.find_one({"_id": user_id})
if len(session.get("google_emails", [])) == 0:
    db.naver_sessions.delete_one({"_id": user_id})
```

## 📝 추가 개선 사항 (향후)

### 1. 세션 관리 UI 개선

세션 카드에 공유 정보 표시:
```jsx
<div className="mt-2">
  <span className="text-xs text-gray-500">
    👥 {session.shared_users_count}명이 사용 중
  </span>
</div>
```

### 2. MongoDB 스키마에 메타데이터 추가

```javascript
{
  "_id": "naver_user_id",
  "google_emails": ["A", "B", "C"],
  "created_by": "A@gmail.com",  // 최초 생성자
  "last_modified_by": "B@gmail.com",  // 마지막 수정자
  "modification_history": [
    { "action": "created", "by": "A", "at": "..." },
    { "action": "added_user", "user": "B", "by": "A", "at": "..." },
    { "action": "removed_user", "user": "C", "at": "..." }
  ]
}
```

### 3. 관리자 기능 추가

- 모든 세션의 공유 현황 보기
- 특정 사용자를 세션에서 강제 제거
- 세션 공유 로그 확인

## 🎉 예상 효과

### 사용자 경험
- ✅ 팀 단위 세션 공유 시 안전한 관리
- ✅ 명확한 피드백 메시지
- ✅ 예상 가능한 동작

### 시스템 안정성
- ✅ 데이터 무결성 유지
- ✅ 다중 사용자 환경 지원
- ✅ 권한 관리 일관성

### 비즈니스 가치
- ✅ 팀/회사 단위 사용 시 더 안전
- ✅ 직원 퇴사 시 간편한 권한 제거
- ✅ 세션 관리 유연성 향상

---

**작성일:** 2024-12-12
**담당자:** AI Assistant
**우선순위:** 🔥 High (다중 사용자 기능 버그)
**상태:** ✅ 수정 완료, 배포 대기





