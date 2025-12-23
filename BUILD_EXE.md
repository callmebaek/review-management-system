# 네이버 세션 생성기 EXE 빌드 가이드

## 🎯 개요

Python 스크립트를 Windows 실행 파일(.exe)로 변환하는 방법입니다.

---

## 📋 준비사항

### 1. Python 설치 (3.11 이상)
- https://www.python.org/downloads/

### 2. 필수 패키지 설치

```bash
cd "c:/Users/smbae/OneDrive/Desktop/work automation/review-management-system"
pip install -r session_creator_requirements.txt
```

---

## 🚀 EXE 빌드 방법

### Option 1: 빠른 빌드 (권장)

```bash
pyinstaller --onefile --windowed --icon=NONE --name="NaverSessionCreator" naver_session_creator.py
```

### Option 2: 상세 옵션 빌드

```bash
pyinstaller --onefile ^
    --windowed ^
    --name="NaverSessionCreator" ^
    --add-data="naver_session_creator.py;." ^
    --hidden-import=selenium ^
    --hidden-import=webdriver_manager ^
    --hidden-import=requests ^
    naver_session_creator.py
```

### Option 3: Spec 파일 사용 (고급)

1. Spec 파일 생성:
```bash
pyinstaller --onefile --windowed naver_session_creator.py
```

2. `NaverSessionCreator.spec` 파일 수정 (필요시)

3. Spec 파일로 빌드:
```bash
pyinstaller NaverSessionCreator.spec
```

---

## 📦 빌드 결과

빌드 완료 후:

```
dist/
  └─ NaverSessionCreator.exe  ← 배포용 파일
```

**파일 크기:** 약 20-30MB (Selenium 포함)

---

## 🧪 테스트

```bash
cd dist
NaverSessionCreator.exe
```

---

## 📤 배포

### 1. 웹 서버에 업로드

`dist/NaverSessionCreator.exe` 파일을 웹 서버에 업로드:

```bash
# 예: Vercel의 public 폴더 또는
# GitHub Releases 또는
# 직접 호스팅
```

### 2. 다운로드 링크 생성

프론트엔드에서 다운로드 버튼:

```html
<a href="/downloads/NaverSessionCreator.exe" download>
  다운로드하기
</a>
```

---

## ⚠️ 주의사항

### Windows Defender 경고

처음 실행 시 "알 수 없는 게시자" 경고가 나타날 수 있습니다:

**해결 방법:**
1. "추가 정보" 클릭
2. "실행" 클릭

**영구 해결 (옵션):**
- 코드 서명 인증서 구매 ($100~$300/년)
- Authenticode로 EXE 서명

---

## 🔧 문제 해결

### 빌드 실패

```bash
# 캐시 삭제 후 재시도
rm -rf build dist __pycache__
pyinstaller --clean naver_session_creator.py
```

### 실행 오류

```bash
# Console 모드로 에러 확인
pyinstaller --onefile --console naver_session_creator.py
```

---

## 📝 버전 관리

### 버전 업데이트 시

1. `naver_session_creator.py`에서 버전 수정
2. 재빌드
3. 파일명에 버전 추가: `NaverSessionCreator_v1.1.exe`

---

## 🎨 아이콘 추가 (선택사항)

### 1. 아이콘 파일 준비
- 파일명: `icon.ico`
- 크기: 256x256 이상

### 2. 빌드 시 아이콘 지정

```bash
pyinstaller --onefile --windowed --icon=icon.ico --name="NaverSessionCreator" naver_session_creator.py
```

---

## 📊 빌드 옵션 설명

| 옵션 | 설명 |
|------|------|
| `--onefile` | 단일 EXE 파일 생성 |
| `--windowed` | 콘솔 창 숨기기 (GUI 앱) |
| `--console` | 콘솔 창 표시 (디버깅용) |
| `--icon=file.ico` | 아이콘 설정 |
| `--name="AppName"` | EXE 파일명 지정 |
| `--hidden-import=module` | 암시적 import 명시 |
| `--add-data="src;dest"` | 추가 파일 포함 |

---

## 🚀 자동화 스크립트

`build.bat` 파일 생성:

```batch
@echo off
echo 🔨 Building Naver Session Creator...

REM Clean previous builds
rmdir /s /q build dist

REM Build EXE
pyinstaller --onefile --windowed --name="NaverSessionCreator" naver_session_creator.py

REM Check result
if exist "dist\NaverSessionCreator.exe" (
    echo ✅ Build successful!
    echo 📦 File location: dist\NaverSessionCreator.exe
) else (
    echo ❌ Build failed!
)

pause
```

실행:
```bash
build.bat
```

---

**빌드 완료 후 사용자에게 배포하세요!** 🎉












