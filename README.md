# WPAA : WebPage Architecture Analyzer

WPAA는 웹 페이지의 HTML 아키텍처를 분석하여 트리 형태로 시각화해주는 툴입니다. 정적 및 동적 웹 페이지의 DOM 구조를 쉽게 파악하고 분석할 수 있습니다.

## 주요 기능

- 웹 페이지의 HTML 구조를 트리 형태로 표현
- 정적 및 동적(JavaScript 렌더링) 웹 페이지 분석 지원
- HTML 캐싱을 통한 성능 최적화
- 비동기 요청 처리로 다중 URL 동시 분석
- 다양한 출력 형식 지원 (텍스트, JSON, PNG 시각화)
- 사용자 정의 필터링 및 속성 포함 기능

## 설치 방법

### 요구사항

```
Python 3.7+
pip install "requirements.txt"
```
graphviz 설치가 필요합니다:
1. [공식 웹사이트](https://graphviz.org/download/)에서 설치 파일을 다운로드하여 설치합니다.
2. graphviz 설치 후, 실행 파일이 있는 bin 디렉토리`(예: C:\Program Files\Graphviz\bin)`를 시스템의 PATH에 추가해야 합니다.


ChromeDriver가 필요합니다(동적 페이지 분석 시):
1. [ChromeDriver 다운로드](https://sites.google.com/a/chromium.org/chromedriver/downloads)
2. 다운로드한 파일을 적절한 위치에 저장
3. 코드 내의 chromedriver 경로 업데이트:
   ```python
   service = Service('your/path/to/chromedriver')
   ```

## 사용 방법

기본 사용법:
```
python wpaa_run.py --urls https://example.com
```

여러 옵션을 사용한 예:
```
python wpaa_run.py --urls https://example.com https://test.com --exclude script style --include-attrs class href --custom-filter "div.content" --max-depth 3 --output json --visualize
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

## 예제

### 기본 분석
```
python wpaa_run.py --urls https://news.ycombinator.com
```

### 동적 콘텐츠 분석 (Selenium 사용)
```
python wpaa_run.py --urls https://www.example.com --use-selenium
```

### 특정 태그 제외하고 시각화
```
python wpaa_run.py --urls https://www.example.com --exclude script style meta link --visualize
```

### 특정 속성 포함 및 JSON 출력
```
python wpaa_run.py --urls https://www.example.com --include-attrs class id href --output json
```

## 구조 설명

- 캐싱: 같은 URL을 반복 분석할 때 성능 최적화
- 비동기 처리: 여러 URL 동시 분석 지원
- 오류 처리: 데코레이터를 통한 일관된 오류 처리
- 트리 구조: anytree 라이브러리를 사용한 HTML DOM 시각화

## 개선 계획

- 트리 비교 기능 추가로 사이트 변경 사항 감지
- 웹 인터페이스 구현
- 더 많은 출력 형식 지원 (SVG, HTML 인터랙티브)
- 성능 최적화 및 메모리 사용량 개선