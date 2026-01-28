---
name: grade-processing
display_name: "성적 처리 & 성적표 생성"
description: "학생 성적 데이터에서 가중 점수를 산출하고, LLM이 개인화된 코멘트와 학습 개입 권고를 생성하여 Excel 성적표를 출력합니다."
tier: full
language: python
tags: [education, grade-report, excel-template, config-driven, 3-phase-pipeline]
input: "CSV/XLSX 성적 데이터 (학번, 이름, 시험 점수, 과제, 출석)"
output: "Excel 성적표 (성적표 + 반 요약 + 관찰 대상) + JSON"
---

# 성적 처리 & 성적표 생성

## 파이프라인 구조

```
[CSV/XLSX 성적 데이터]
        │
   Phase 1-1: convert.py (Script)
   │  CSV/XLSX → JSON 변환
        │
   Phase 1-2: extract.py (Script)
   │  가중 점수 산출, 등급 배정, 관찰 대상 식별
        │
   Phase 2: LLM Judgment
   │  개인화 코멘트, 학습 개입 권고, 반 인사이트
        │
   Phase 3: generate.py (Script)
   │  templates/template.xlsx 로드 → 헤더 동적 읽기 → 데이터 채우기
        │
[Excel 성적표 + JSON]
```

## 역할 분리

### Script (결정적)
- CSV/XLSX 파싱 및 데이터 변환
- 가중 평균 산출 (config 기반 가중치)
- 등급 배정 (config 기반 등급 기준)
- 관찰 대상 식별 (총점 미달, 출석 부족, 성적 급락)
- **Excel 템플릿 기반 보고서 생성**

### LLM (판단)
- 학생별 개인화 코멘트 생성 (성과 패턴 분석)
- 관찰 대상 학생 개입 권고 (맞춤형 조치 제안)
- 반 전체 인사이트 (등급 분포, 교수법 개선)

## Phase 2: LLM 판단 가이드

### 코멘트 생성 기준
- 시험 성적 변화 추이 (중간 → 기말)
- 과제 vs 시험 성적 격차
- 출석과 성적 상관관계
- 강점 우선, 개선점은 건설적으로

### 관찰 대상 판단
- `issues`에 명시된 문제 유형별 맞춤 권고
- 총점 미달: 보충 학습 계획
- 출석 부족: 면담 → 원인 파악 → 지원
- 성적 급락: 추세 분석 → 원인 분석

## Excel 템플릿 패턴

### 핵심 원리
> **템플릿은 일반 사용자(교사)가 편집 가능**

- `templates/template.xlsx`를 직접 열어 수정 가능
- 열 추가/삭제/이름변경 → generate.py가 자동 적응
- 서식(색상, 테두리, 글꼴) 변경 → 출력에 그대로 반영
- 시트 이름 변경 → `config/settings.yaml`에서 매핑

### generate.py 동작 방식
```python
# 1. 템플릿 로드
wb = load_workbook("templates/template.xlsx")

# 2. 헤더 동적 읽기 (사용자가 변경해도 자동 적응)
headers = parse_headers(ws, header_row=4)
# → {"학번": 1, "이름": 2, "중간고사": 3, ...}

# 3. 필드 매핑으로 데이터 채우기
REPORT_FIELD_MAP = {"학번": "student_id", "이름": "name", ...}

# 4. 서식 보존하며 셀 쓰기
copy_cell_style(ref_cell, target_cell)
ws.cell(row=row, column=col, value=data)
```

## 파일 구조

```
grade-processing/
├── SKILL.md
├── config/settings.yaml          # 가중치, 등급 기준, 임계값, 템플릿 설정
├── references/schemas.md         # 데이터 스키마
├── scripts/
│   ├── convert.py                # Phase 1-1: CSV/XLSX → JSON
│   ├── extract.py                # Phase 1-2: 점수 산출, 등급 배정
│   └── generate.py               # Phase 3: Excel 템플릿 → 보고서
├── templates/
│   └── template.xlsx             # ★ 사용자 편집 가능한 Excel 템플릿
├── sample/
│   └── grades.csv                # 테스트 데이터
└── preset-prompt.md              # AIP Phase 2 프롬프트
```

## 실행 방법

```bash
# Phase 1-1: 입력 변환
python scripts/convert.py --input sample/grades.csv --output output/raw_data.json

# Phase 1-2: 점수 산출
python scripts/extract.py --raw-data output/raw_data.json --config config/settings.yaml --output output/extracted_data.json

# Phase 2: LLM 판단 (AIP 또는 수동)
# → output/judged_data.json

# Phase 3: 보고서 생성
python scripts/generate.py --judged-data output/judged_data.json --output-dir output/
```
