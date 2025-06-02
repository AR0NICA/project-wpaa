# WPAA 설치 및 설정 가이드

## 빠른 시작

### 1. 필수 패키지 설치

```powershell
# Python 패키지 설치
pip install -r requirements.txt
```

### 2. 기능 테스트 실행

```powershell
python test_wpaa.py
```

### 3. 웹 인터페이스 실행

```powershell
python run_web_interface.py
```

브라우저에서 `http://127.0.0.1:5000`에 접속하세요.

## 상세 설치 가이드

### 1. Python 환경 확인

```powershell
python --version
```

Python 3.7 이상이 필요합니다.

### 2. 가상환경 생성 (권장)

```powershell
# 가상환경 생성
python -m venv wpaa_env

# 가상환경 활성화
wpaa_env\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. Graphviz 설치

1. [Graphviz 공식 웹사이트](https://graphviz.org/download/)에서 Windows용 설치 파일 다운로드
2. 설치 후 시스템 PATH에 bin 디렉토리 추가
   - 예: `C:\Program Files\Graphviz\bin`

### 4. ChromeDriver 설치 (선택사항)

동적 웹 페이지 분석을 위해 필요합니다.

1. [ChromeDriver 다운로드](https://sites.google.com/chromium.org/driver/)
2. Chrome 버전과 호환되는 버전 선택
3. 실행 파일을 PATH에 추가하거나 프로젝트 디렉토리에 저장

## 사용법

### 웹 인터페이스 (권장)

```powershell
python run_web_interface.py
```

### 명령줄 인터페이스

```powershell
# 기본 분석
python wpaa_run.py --urls https://example.com

# 고급 옵션
python wpaa_run.py --urls https://example.com --export-html --compare-changes --show-performance
```

## 문제 해결

### ImportError 발생 시

```powershell
pip install --upgrade -r requirements.txt
```

### Graphviz 관련 오류

1. Graphviz가 올바르게 설치되었는지 확인
2. PATH 환경변수에 Graphviz bin 디렉토리가 추가되었는지 확인

### ChromeDriver 관련 오류

1. Chrome 브라우저가 설치되어 있는지 확인
2. ChromeDriver와 Chrome 버전이 호환되는지 확인
3. ChromeDriver가 PATH에 있는지 확인

## 기능별 사용 예제

### 1. 기본 웹 페이지 분석

```powershell
python wpaa_run.py --urls https://news.ycombinator.com
```

### 2. 인터랙티브 HTML 출력

```powershell
python wpaa_run.py --urls https://github.com --export-html
```

### 3. 변경사항 추적

```powershell
# 첫 번째 실행 (스냅샷 생성)
python wpaa_run.py --urls https://example.com --compare-changes

# 두 번째 실행 (변경사항 감지)
python wpaa_run.py --urls https://example.com --compare-changes
```

### 4. 성능 최적화된 분석

```powershell
python wpaa_run.py --urls https://example.com --exclude script style meta --max-depth 5 --show-performance
```

## 출력 파일

분석 후 생성되는 파일들:

- `tree_*.svg` - SVG 형식 트리 구조
- `tree_*.html` - 인터랙티브 HTML 뷰어
- `tree_*.csv` - CSV 형식 데이터
- `tree_*.md` - 마크다운 보고서
- `cache/` - HTML 캐시 파일들
- `snapshots/` - 변경사항 추적을 위한 스냅샷들