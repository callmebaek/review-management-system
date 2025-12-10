# Windows 설정 가이드

## ⚠️ Python 버전 확인

현재 Python 3.14를 사용 중이시네요. 안정성을 위해 **Python 3.9-3.12** 사용을 권장합니다.

```powershell
python --version
```

Python 3.14는 최신 버전이라 일부 패키지가 호환되지 않을 수 있습니다.

---

## 🔧 올바른 설치 방법 (Windows PowerShell)

### 1. 프로젝트 디렉토리로 이동

```powershell
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"
```

### 2. 가상환경 생성

```powershell
python -m venv venv
```

### 3. 가상환경 활성화 (Windows)

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**만약 권한 오류가 발생하면:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

**또는 CMD:**
```cmd
venv\Scripts\activate.bat
```

### 4. pip 업그레이드

```powershell
python -m pip install --upgrade pip
```

### 5. 의존성 설치

```powershell
pip install -r requirements.txt
```

### 6. Playwright 브라우저 설치

```powershell
playwright install chromium
```

---

## 🐛 문제 해결

### "pydantic-core 빌드 실패" 오류

**원인:** Python 3.14와 pydantic 버전 호환성 문제

**해결책 1: pydantic 버전 업그레이드 (권장)**
```powershell
pip install --upgrade pydantic pydantic-settings
```

**해결책 2: Python 다운그레이드**
- Python 3.11 또는 3.12 설치: https://www.python.org/downloads/
- 가상환경 재생성

### "Rust 컴파일러 필요" 오류

**해결책:** Pre-built wheel 사용
```powershell
pip install --upgrade pip
pip install pydantic==2.10.4 --prefer-binary
```

### "source 명령 없음" 오류

**Windows에서는:**
- PowerShell: `.\venv\Scripts\Activate.ps1`
- CMD: `venv\Scripts\activate.bat`

### "ExecutionPolicy" 오류

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## ✅ 설치 확인

가상환경이 활성화되면 프롬프트에 `(venv)` 표시가 나타납니다:

```
(venv) PS C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend>
```

패키지 설치 확인:
```powershell
pip list
```

---

## 🚀 서버 실행

가상환경 활성화 후:

```powershell
python -m backend.main
```

또는:

```powershell
uvicorn backend.main:app --reload --port 8000
```

---

## 📝 완전한 설치 스크립트 (한 번에 실행)

```powershell
# 1. 디렉토리 이동
cd "C:\Users\smbae\OneDrive\Desktop\work automation\review machine\backend"

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 4. pip 업그레이드
python -m pip install --upgrade pip

# 5. 의존성 설치
pip install -r requirements.txt

# 6. Playwright 설치
playwright install chromium

# 7. 서버 실행
python -m backend.main
```

---

## 🔍 현재 문제 분석

터미널 출력을 보면:
1. ✅ pip 다운로드는 성공
2. ❌ pydantic-core 빌드 실패 (Rust PATH 문제)
3. ❌ playwright 명령 실행 불가 (설치 실패)

**추천 해결책:**

1. requirements.txt의 pydantic 버전이 업데이트되었습니다 (2.10.4)
2. 다음 명령어로 재시도:

```powershell
# 기존 설치 시도 정리
pip cache purge

# pip 업그레이드
python -m pip install --upgrade pip

# 개별 패키지 먼저 설치 (pre-built wheel 우선)
pip install pydantic==2.10.4 --prefer-binary
pip install pydantic-settings==2.7.0

# 나머지 의존성 설치
pip install -r requirements.txt

# Playwright 설치
playwright install chromium
```

---

## 💡 추가 팁

### 가상환경 비활성화
```powershell
deactivate
```

### 가상환경 삭제 후 재생성
```powershell
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Python 버전 확인
```powershell
python --version
# Python 3.9-3.12 권장
```








