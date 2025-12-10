# 🚀 프론트엔드 서버 시작 가이드

## ⚠️ 현재 상황

PowerShell에서 npm 명령 출력이 제대로 캡처되지 않고 있습니다.
직접 터미널에서 실행해주세요!

---

## ✅ 해결 방법 (간단!)

### 방법 1: 새 PowerShell 터미널 열기

1. **새 PowerShell 터미널 열기** (Cursor 또는 Windows Terminal)

2. **다음 명령어 복사해서 붙여넣기:**

```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\frontend"
npm install
npm run dev
```

3. **완료!** 

출력에서 다음과 같은 메시지가 보이면 성공:
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

4. **브라우저에서 http://localhost:5173 접속**

---

### 방법 2: CMD 사용

1. **CMD 열기** (명령 프롬프트)

2. **다음 명령어 실행:**

```cmd
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\frontend"
npm install
npm run dev
```

---

## 🔍 확인 사항

### npm install이 제대로 실행되었는지 확인:

```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\frontend"
dir node_modules
```

`node_modules` 폴더가 있고 많은 파일들이 있어야 합니다.

### 없으면 다시 설치:

```powershell
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue
npm cache clean --force
npm install
```

---

## 🎯 빠른 시작 (올인원)

**PowerShell에서 한 줄로:**

```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\frontend" ; if (!(Test-Path node_modules)) { npm install } ; npm run dev
```

---

## 백엔드도 함께 시작

**백엔드 서버** (별도 터미널):
```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"
python -m backend.main
```

**백엔드 URL:** http://localhost:8000

---

## 📱 서버 접속

### 프론트엔드
- http://localhost:5173

### 백엔드
- http://localhost:8000
- http://localhost:8000/docs (API 문서)

---

## 🛑 서버 종료

- 터미널에서 `Ctrl + C` 누르기
- 또는 터미널 창 닫기

---

## 💡 문제 해결

### "Cannot find module" 오류

```powershell
cd frontend
Remove-Item node_modules -Recurse -Force
npm install
```

### 포트 이미 사용 중

다른 프로그램이 5173 포트를 사용 중입니다:

```powershell
# 포트 사용 중인 프로세스 찾기
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue

# 또는 다른 포트 사용
npm run dev -- --port 3000
```

### npm 명령이 느림

```powershell
npm cache clean --force
npm install
```

---

## ✅ 성공 확인

브라우저에서 http://localhost:5173 을 열면:

**"리뷰 관리 시스템" 로그인 페이지가 보여야 합니다!**

"Google 계정으로 로그인" 버튼이 보이면 성공! 🎉

---

## 다음 단계

1. ✅ 프론트엔드 실행 완료
2. ⏳ `.env` 파일 설정 (`SETUP_GUIDE.md` 참고)
3. ⏳ Google OAuth 설정
4. ⏳ OpenAI API 키 설정
5. 🚀 리뷰 관리 시작!







