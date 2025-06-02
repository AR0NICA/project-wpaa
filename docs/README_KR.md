# WPAA : WebPage Architecture Analyzer

WPAA는 웹 페이지의 HTML 아키텍처를 분석하여 트리 형태로 시각화해주는 툴입니다. 정적 및 동적 웹 페이지의 DOM 구조를 쉽게 파악하고 분석할 수 있습니다.

## 주요 기능

- 🌳 **트리 시각화**: 웹 페이지의 HTML 구조를 트리 형태로 표현
- 🔄 **변경사항 추적**: 웹 페이지 구조의 변경사항을 자동으로 감지하고 비교
- 🌐 **웹 인터페이스**: 직관적인 웹 UI를 통한 쉬운 분석
- 📊 **다양한 출력 형식**: SVG, 인터랙티브 HTML, CSV, 마크다운 등 지원
- ⚡ **성능 최적화**: 비동기 처리, 캐싱, 메모리 최적화로 빠른 분석
- 🔧 **정적/동적 분석**: JavaScript 렌더링 웹 페이지까지 지원
- 🎯 **사용자 정의 필터링**: CSS 셀렉터와 속성 필터링 기능
- 📈 **성능 모니터링**: 실행 시간, 메모리 사용량, 캐시 효율성 추적

## 설치 방법

[설치 가이드](docs/SETUP_KR.md)

### 요구사항

```
Python 3.7+
pip install -r requirements.txt
```

**필수 외부 프로그램:**

1. **Graphviz 설치**:
   - [공식 웹사이트](https://graphviz.org/download/)에서 설치 파일을 다운로드하여 설치
   - graphviz 설치 후, 실행 파일이 있는 bin 디렉토리`(예: C:\Program Files\Graphviz\bin)`를 시스템의 PATH에 추가

2. **ChromeDriver 설치** (동적 페이지 분석 시):
   - [ChromeDriver 다운로드](https://sites.google.com/a/chromium.org/chromedriver/downloads)
   - 다운로드한 파일을 적절한 위치에 저장
   - 코드 내의 chromedriver 경로 업데이트:
     ```python
     service = Service('your/path/to/chromedriver')
     ```

## 사용 방법

### 1. 웹 인터페이스 사용 (권장)

```bash
python run_web_interface.py
```

브라우저에서 `http://127.0.0.1:5000`에 접속하여 직관적인 웹 UI를 통해 분석을 수행할 수 있습니다.

**웹 인터페이스 기능:**
- 📱 사용자 친화적인 웹 UI
- 🔄 실시간 분석 진행 상황 표시
- 📊 다양한 출력 형식 다운로드
- 🔍 변경사항 비교 기능
- 📈 성능 통계 확인

### 2. 명령줄 인터페이스 사용

기본 사용법:
```bash
python wpaa_run.py --urls https://example.com
```

고급 옵션 사용:
```bash
python wpaa_run.py --urls https://example.com https://test.com \
  --exclude script style \
  --include-attrs class href \
  --custom-filter "div.content" \
  --max-depth 3 \
  --export-html \
  --compare-changes \
  --show-performance
```

## 명령줄 옵션

- `--urls`: 분석할 웹 페이지 URL 목록 (필수)
- `--use-selenium`: Selenium으로 동적 콘텐츠 가져오기
- `--exclude`: 제외할 HTML 태그 목록 (예: script style)
- `--include-attrs`: 노드에 포함할 HTML 속성 (예: class id href)
- `--custom-filter`: CSS 셀렉터로 특정 요소만 필터링 (예: div.classname)
- `--max-depth`: 트리의 최대 깊이 제한
- `--include-text`: 텍스트 콘텐츠 포함
- `--output`: 출력 형식 선택 (text 또는 json)
- `--visualize`: PNG 파일로 트리 구조 시각화
- `--export-svg`: SVG 형식으로 출력
- `--export-html`: 인터랙티브 HTML로 출력
- `--export-csv`: CSV 형식으로 출력
- `--export-markdown`: 마크다운 형식으로 출력
- `--compare-changes`: 이전 버전과 변경사항 비교
- `--show-performance`: 성능 보고서 표시
- `--optimize-tree`: 트리 구조 최적화

## 예제

### 기본 분석
```bash
python wpaa_run.py --urls https://news.ycombinator.com
```

### 동적 콘텐츠 분석 (Selenium 사용)
```bash
python wpaa_run.py --urls https://www.example.com --use-selenium
```

### 특정 태그 제외하고 시각화
```bash
python wpaa_run.py --urls https://www.example.com --exclude script style meta link --visualize
```

### 특정 속성 포함 및 JSON 출력
```bash
python wpaa_run.py --urls https://www.example.com --include-attrs class id href --output json
```

### 인터랙티브 HTML 및 변경사항 비교
```bash
python wpaa_run.py --urls https://www.example.com --export-html --compare-changes --show-performance
```

### 다양한 출력 형식으로 내보내기
```bash
python wpaa_run.py --urls https://www.example.com --export-svg --export-csv --export-markdown
```

## 구조 설명

- 캐싱: 같은 URL을 반복 분석할 때 성능 최적화
- 비동기 처리: 여러 URL 동시 분석 지원
- 오류 처리: 데코레이터를 통한 일관된 오류 처리
- 트리 구조: anytree 라이브러리를 사용한 HTML DOM 시각화

## 개선 계획
MK-II_2523 : 기능 개선 완료
- [X] 트리 비교 기능 추가로 사이트 변경 사항 감지
- [X] 웹 인터페이스 구현
- [X] 더 많은 출력 형식 지원 (SVG, HTML 인터랙티브)
- [X] 성능 최적화 및 메모리 사용량 개선