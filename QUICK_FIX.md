# 🚨 빠른 해결 가이드

## 문제: Python 3.14 + pydantic 호환성

Python 3.14는 매우 최신 버전이라 pydantic-core가 pre-built wheel을 제공하지 않아 Rust 컴파일이 필요합니다.

---

## ✅ 해결책 1: Rust PATH 설정 (빠름)

Rust가 설치되었지만 PATH에 없습니다. PowerShell을 **관리자 권한**으로 다시 시작한 후:

```powershell
# Rust를 PATH에 추가
$env:Path += ";C:\Users\smbae\.cargo\bin"
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\smbae\.cargo\bin", [System.EnvironmentVariableTarget]::User)

# PowerShell 재시작 후
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"
pip install -r requirements.txt
playwright install chromium
```

---

## ✅ 해결책 2: Python 다운그레이드 (권장)

Python 3.11 또는 3.12로 다운그레이드하는 것이 가장 안전합니다.

### 1. Python 3.12 다운로드
https://www.python.org/downloads/release/python-3120/
- "Windows installer (64-bit)" 다운로드

### 2. 설치 옵션
- ✅ "Add Python to PATH" 체크
- ✅ "Install for all users" 선택 (선택사항)

### 3. 가상환경 재생성
```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"

# 기존 가상환경 삭제
Remove-Item -Recurse -Force venv

# Python 3.12로 가상환경 생성
py -3.12 -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt
playwright install chromium
```

---

## ✅ 해결책 3: 가상환경 없이 실행 (임시)

일단 테스트하려면 가상환경 없이 직접 설치:

```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"

# 전역으로 설치 (권장하지 않음)
pip install -r requirements.txt --user
playwright install chromium

# 서버 실행
python -m backend.main
```

---

## ✅ 해결책 4: Docker 사용 (고급)

Docker Desktop이 설치되어 있다면:

```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine"

# Dockerfile 생성 (이미 생성됨)
docker build -t review-system .
docker run -p 8000:8000 -p 5173:5173 review-system
```

---

## 🎯 추천 순서

1. **해결책 2 (Python 3.12)** ← 가장 안정적
2. **해결책 1 (Rust PATH)** ← 빠르지만 추가 문제 가능
3. **해결책 3 (임시 테스트용)** ← 테스트만 하려는 경우
4. **해결책 4 (Docker)** ← 고급 사용자

---

## 💡 현재 상황 확인

```powershell
# Python 버전 확인
python --version

# Rust 설치 확인
cargo --version

# PATH 확인
$env:Path
```

---

## 🔄 다음 단계 (Python 3.12 설치 후)

```powershell
# 1. 디렉토리 이동
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"

# 2. 가상환경 생성 (Python 3.12)
py -3.12 -m venv venv

# 3. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 4. 의존성 설치
pip install -r requirements.txt

# 5. Playwright 설치
playwright install chromium

# 6. 서버 실행
python -m backend.main
```

프롬프트에 `(venv)`가 표시되면 성공입니다!

---

## ❓ 여전히 문제가 있다면

1. PowerShell을 **관리자 권한**으로 실행
2. ExecutionPolicy 설정:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. 위 명령어들을 다시 실행

또는 간단하게 CMD (명령 프롬프트)를 사용:
```cmd
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
playwright install chromium
python -m backend.main
```








