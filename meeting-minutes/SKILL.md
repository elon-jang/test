---
name: meeting-minutes
display_name: "회의록 처리 & 액션 아이템 추적"
description: "회의 녹취록/메모에서 액션 아이템을 자동 식별하고, 담당자·우선순위를 추론하여 구조화된 보고서를 생성합니다."
version: "1.0.0"
author: "elon"
tier: full
language: python
tags:
  - meeting-minutes
  - action-items
  - text-processing
  - llm-judgment
  - report-generation
---

# 회의록 처리 & 액션 아이템 추적 스킬

## 개요

회의 녹취록 또는 메모 텍스트에서 참석자, 의사결정, 액션 아이템을 자동 추출하고,
LLM이 암시적 액션 아이템과 담당자를 추론하여 구조화된 보고서를 생성하는 파이프라인입니다.

## 역할 분배 원칙

| 담당 | 역할 | 설명 |
|------|------|------|
| **Script** | 결정적 처리 | 텍스트 파싱, 키워드 매칭, 포맷 변환, 보고서 생성 |
| **LLM** | 판단·추론 | 암시적 액션 아이템 식별, 담당자 추론, 우선순위 결정, 요약 |

## Input

| 파일 | 형식 | 설명 |
|------|------|------|
| 회의록 (Meeting Notes) | `.txt` / `.docx` | 회의 녹취록 또는 메모 |
| 프로젝트 트래커 (선택) | `.json` | 기존 액션 아이템 목록 (ID, 담당자, 마감일) |

## Output

| 파일 | 형식 | 설명 |
|------|------|------|
| `action_report.json` | JSON | 구조화된 액션 아이템 보고서 |
| `action_report.md` | Markdown | 사람이 읽기 쉬운 보고서 |

## Execution Flow

```
[회의록.txt/.docx]
       │
       ▼
┌─────────────────────┐
│ Phase 1-1: convert  │  Script (convert.py)
│ DOCX → Markdown     │  markitdown 또는 텍스트 복사
└─────────┬───────────┘
          │  converted.md
          ▼
┌─────────────────────┐
│ Phase 1-2: extract  │  Script (extract.py)
│ 키워드 매칭 추출     │  config/settings.yaml 기반
└─────────┬───────────┘
          │  raw_data.json
          ▼
┌─────────────────────┐
│ Phase 2: judgment   │  ★ LLM
│ 액션아이템 식별      │  암시적 항목, 담당자 추론
│ 우선순위·분류        │  맥락 기반 판단
└─────────┬───────────┘
          │  judged_data.json
          ▼
┌─────────────────────┐
│ Phase 3: generate   │  Script (generate.py)
│ 보고서 생성          │  JSON + Markdown 출력
└─────────┬───────────┘
          │
          ▼
[action_report.json / .md]
```

## Phase별 상세

### Phase 1-1: Input Conversion (convert.py)

```bash
python scripts/convert.py \
  --meeting-notes sample/meeting-notes.txt \
  --output-dir work/converted
```

- `.txt` → 그대로 복사
- `.docx` → `markitdown`으로 Markdown 변환
- 출력: `work/converted/meeting_notes.md`

### Phase 1-2: Data Extraction (extract.py)

```bash
python scripts/extract.py \
  --converted work/converted/meeting_notes.md \
  --tracker sample/project-tracker.json \
  --output work/raw_data.json
```

- `config/settings.yaml`의 키워드로 매칭:
  - **참석자**: "참석:", "참석자:", "Attendees:" 패턴
  - **명시적 액션 아이템**: "할 일:", "TODO:", "액션:", "담당:" 패턴
  - **의사결정**: "결정:", "합의:", "Decided:" 패턴
  - **일정**: 날짜 패턴 (YYYY-MM-DD, M/D)
- 기존 트래커의 액션 아이템 ID 언급 감지
- 출력: `raw_data.json` (참석자, 명시적 항목, 의사결정, 일정, 원문 섹션)

### Phase 2: LLM Judgment

`raw_data.json`을 읽고 다음을 수행:

1. **암시적 액션 아이템 식별**: 명시적으로 "할 일"로 표기되지 않았지만 토론 맥락상 액션이 필요한 항목
   - 예: "이 부분은 홍길동씨가 확인해보면 좋겠네요" → 액션 아이템
2. **담당자 추론**: "~씨가 처리", "~팀에서 검토" 등 맥락에서 담당자 결정
3. **우선순위 결정**: 긴급도·중요도 기반 (High / Medium / Low)
4. **카테고리 분류**: development, design, review, research, admin
5. **의사결정 요약**: 핵심 결정 사항을 1-2문장으로 요약
6. **미결 항목 플래그**: 결론 없이 끝난 토론 항목 식별

**LLM 출력**: `judged_data.json` (references/schemas.md의 Schema A 참조)

### Phase 3: Report Generation (generate.py)

```bash
python scripts/generate.py \
  --judged-data work/judged_data.json \
  --output-dir output
```

- `judged_data.json` → `action_report.json` + `action_report.md`
- Markdown 보고서 포함 내용:
  - 회의 요약 (일시, 참석자)
  - 의사결정 목록
  - 액션 아이템 테이블 (ID, 제목, 담당자, 우선순위, 카테고리, 마감일)
  - 미결 항목
  - 기존 트래커 업데이트 사항
