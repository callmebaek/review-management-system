# 긴급 수정: 답글 쓰기 버튼 클릭 추가

## 파일
`backend/services/naver_automation_selenium.py`

## 함수
`def post_reply_by_author_date(...)` (약 1041줄 시작)

## 찾을 부분
```python
# Scroll to review
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_review)
time.sleep(1)

# Fill textarea (JavaScript)  ← 여기 바로 위에 추가!
print("⌨️  Waiting for textarea...")
```

## 추가할 코드
```python
# 🚀 CRITICAL: "답글 쓰기" 버튼 클릭 (이게 없어서 답글 안 올라감!)
print("🖱️  Clicking '답글 쓰기' button...")
reply_btn = target_review.find_element(By.XPATH, ".//button[contains(., '답글')]")
driver.execute_script("arguments[0].click();", reply_btn)
time.sleep(2)
print("✅ Reply form opened")
```

## 완성 코드
```python
# Scroll to review
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_review)
time.sleep(1)

# 🚀 답글 쓰기 버튼 클릭
print("🖱️  Clicking '답글 쓰기' button...")
reply_btn = target_review.find_element(By.XPATH, ".//button[contains(., '답글')]")
driver.execute_script("arguments[0].click();", reply_btn)
time.sleep(2)
print("✅ Reply form opened")

# Fill textarea (JavaScript)
print("⌨️  Waiting for textarea...")
textarea = WebDriverWait(driver, 10).until(...)
```

---

## 중복 알림 문제

`frontend/src/pages/Reviews.jsx`의 `handleReplyPosted` 함수에서:

```javascript
const handleReplyPosted = async () => {
  if (platform === 'gbp') {
    refetchGBP()
  } else {
    // ❌ 이 alert 제거!
    // alert('✅ 답글이 등록되었습니다. 잠시 후 새로고침합니다.')
    
    setTimeout(() => {
      refetchNaver().catch(...)
    }, 3000)
  }
}
```

---

**이 2가지를 수정해주세요!**




