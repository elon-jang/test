# AIP Skill 작성 가이드: 4대 판단 패턴 편

> Invoice Classification Skill을 예시로 한 실전 교육 자료
>
> **이 가이드의 초점**: Mapping Table, Decision Tree, Before/After Examples, Excel Template — 4가지 판단 패턴을 하나의 Skill에 통합하는 방법

---

## 목차

1. [기본 가이드와의 관계](#1-기본-가이드와의-관계)
2. [4대 판단 패턴 개요](#2-4대-판단-패턴-개요)
3. [패턴 1: Mapping Table](#3-패턴-1-mapping-table)
4. [패턴 2: Decision Tree](#4-패턴-2-decision-tree)
5. [패턴 3: Before/After Examples](#5-패턴-3-beforeafter-examples)
6. [패턴 4: Excel Template (Human-Editable)](#6-패턴-4-excel-template-human-editable)
7. [4패턴 통합 설계](#7-4패턴-통합-설계)
8. [config 설계: 패턴별 영역 분리](#8-config-설계-패턴별-영역-분리)
9. [extract.py: Mapping + Decision Tree 구현](#9-extractpy-mapping--decision-tree-구현)
10. [generate.py: Excel Template 구현](#10-generatepy-excel-template-구현)
11. [preset-prompt.md: LLM에게 패턴 위임](#11-preset-promptmd-llm에게-패턴-위임)
12. [판단 패턴 선택 가이드](#12-판단-패턴-선택-가이드)
13. [체크리스트](#13-체크리스트)

---

## 1. 기본 가이드와의 관계

이 문서는 `skill-authoring-guide.md`(T-Connect 기본편)의 **확장판**입니다.

| 항목 | 기본편 (T-Connect) | 이 가이드 (Invoice Classification) |
|------|-------------------|-----------------------------------|
| 초점 | Skill 구조, SKILL.md 작성법, 역할 분리 | **4대 판단 패턴**의 설계와 구현 |
| 대상 독자 | Skill을 처음 만드는 사람 | 판단 로직을 고도화하려는 사람 |
| 전제 | 없음 | 기본편 숙지 |
| 예시 Skill | T-Connect (일본어 Excel 분석) | Invoice Classification (경비 분류) |

기본편에서 다룬 내용(Frontmatter, Execution Flow, CLI 표준화, 언어 지원 등)은 반복하지 않습니다.

---

## 2. 4대 판단 패턴 개요

Skill에서 LLM의 판단을 구조화하는 4가지 패턴:

```
┌─────────────────────────────────────────────────────────────────┐
│                     4대 판단 패턴                                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ Mapping Table│  │Decision Tree │  ← Script이 수행 (Phase 1)  │
│  │ 입력→카테고리  │  │ 조건→플래그   │                             │
│  └──────┬───────┘  └──────┬───────┘                             │
│         │                 │                                     │
│         ▼                 ▼                                     │
│  ┌──────────────────────────────┐                               │
│  │   Before/After Examples     │  ← LLM이 참조 (Phase 2)       │
│  │   판단 톤 + 예외 처리 보정    │                               │
│  └──────────────┬──────────────┘                                │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────┐                               │
│  │   Excel Template            │  ← Script이 수행 (Phase 3)    │
│  │   사람이 편집 가능한 출력 양식  │                               │
│  └──────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### 각 패턴의 역할

| 패턴 | 담당 | 위치 | 핵심 질문 |
|------|------|------|----------|
| Mapping Table | Script | config/settings.yaml | "이 입력은 어떤 카테고리인가?" |
| Decision Tree | Script | config/settings.yaml + extract.py | "이 항목에 이상이 있는가?" |
| Before/After Examples | LLM | references/examples.md | "판단의 톤과 수준은 어떠해야 하는가?" |
| Excel Template | Script | templates/template.xlsx | "출력을 어떤 양식으로 내보내는가?" |

### 핵심 통찰

> **Script은 1차 분류, LLM은 최종 판단.**
>
> Script이 Mapping Table과 Decision Tree로 "힌트"를 생성하면,
> LLM이 Before/After Examples를 참고하여 "확정"한다.
> Excel Template은 확정된 결과를 사람이 읽기 좋은 양식으로 변환한다.

---

## 3. 패턴 1: Mapping Table

### 정의

**입력값의 키워드를 기준으로 카테고리를 결정하는 룩업 테이블.**

### Invoice Classification의 실제 구현

#### config/settings.yaml

```yaml
gl_accounts:
  교통비:
    code: "GL-5100"
    description: "출장/교통비"
    keywords: [택시, KTX, 기차, 버스, 항공, 주차, 톨게이트, 고속도로, 대리운전]
  식비:
    code: "GL-5300"
    description: "복리후생/식비"
    keywords: [식사, 회식, 점심, 저녁, 커피, 카페, 식당, 배달, 음료]
  소프트웨어:
    code: "GL-5200"
    description: "소프트웨어/라이선스"
    keywords: [구독, 라이선스, SaaS, 클라우드, AWS, Azure, Adobe, Figma, Slack, Notion]
  사무용품:
    code: "GL-5400"
    description: "소모품/사무용품"
    keywords: [용지, 토너, 펜, 노트, 문구, 프린터, 잉크, USB, 케이블]
  숙박비:
    code: "GL-5110"
    description: "출장숙박비"
    keywords: [호텔, 숙박, 모텔, 게스트하우스, 에어비앤비]
  교육비:
    code: "GL-5500"
    description: "교육/세미나"
    keywords: [교육, 세미나, 컨퍼런스, 워크숍, 수강, 자격증]
  기타:
    code: "GL-5900"
    description: "기타 경비"
    keywords: []                          # ← 빈 키워드 = Fallback
```

#### extract.py의 매칭 함수

```python
def match_category(vendor: str, description: str, gl_accounts: dict) -> tuple:
    """
    ★ Mapping Table lookup: keywords → category + GL code.
    """
    text = (vendor + " " + description).lower()
    for category, info in gl_accounts.items():
        for keyword in info.get("keywords", []):
            if keyword.lower() in text:
                return category, info["code"]
    return "기타", gl_accounts.get("기타", {}).get("code", "GL-5900")
```

### 설계 원칙

**원칙 1: Script은 "힌트"만 생성**

```python
# extract.py — 결과를 category_hint로 저장 (확정이 아님)
item["category_hint"] = cat
item["gl_code_hint"] = gl_code
```

"hint" 접미사가 핵심. LLM이 이것을 검증/재분류할 수 있다는 의미.

```
# BAD: Script이 확정하면 LLM이 개입할 여지가 없음
item["category"] = cat

# GOOD: hint라는 명명으로 LLM 재분류 가능성을 열어둠
item["category_hint"] = cat
```

**원칙 2: Fallback 카테고리 필수**

키워드에 매칭되지 않는 항목이 반드시 존재. "기타" 카테고리가 Fallback:

```yaml
기타:
  code: "GL-5900"
  keywords: []           # 빈 키워드 = 모든 미매칭 항목이 여기로
```

LLM이 "기타"로 분류된 항목을 재분류하는 것이 가장 가치 있는 판단:

```
Input:  vendor="교보문고", description="업무 참고 도서 3권"
Script: category_hint="기타" (키워드 매칭 실패)
LLM:    category="교육비" (vendor+description 의미 분석)
```

**원칙 3: 검색 대상 = vendor + description 결합**

```python
text = (vendor + " " + description).lower()
```

vendor만으로는 부족한 경우가 많음:
- "쿠팡" → 사무용품? 식품? 전자제품? (description 확인 필요)
- "스타벅스 강남역점" → vendor만으로 "식비" 판단 가능

### Mapping Table 작성 체크리스트

- [ ] 키워드가 중복되지 않는가? (여러 카테고리에 동일 키워드 → 첫 번째가 매칭)
- [ ] Fallback 카테고리가 있는가?
- [ ] 결과가 "hint"로 저장되어 LLM 재분류가 가능한가?
- [ ] 키워드는 대소문자 무관하게 매칭되는가?
- [ ] 반각/전각 구분이 필요한 키워드가 있는가?

---

## 4. 패턴 2: Decision Tree

### 정의

**조건 분기로 항목의 이상 여부를 플래그로 분류하는 판단 로직.**

### Invoice Classification의 Decision Tree

#### SKILL.md에 기술된 트리

```
경비 항목
├─ 금액 > 카테고리별 한도?
│  └─ YES → OVER_LIMIT
├─ 동일 날짜 + 동일 금액 존재?
│  └─ YES → DUPLICATE_SUSPECT
├─ 카테고리 평균 × 3배 초과?
│  └─ YES → OUTLIER
└─ 해당 없음 → NONE
```

#### config/settings.yaml의 판단 기준

```yaml
policy:
  limits:                           # Branch 1: 한도 초과
    교통비: 200000
    식비: 100000
    소프트웨어: 500000
    사무용품: 300000
    숙박비: 150000
    교육비: 1000000
    기타: 100000
  duplicate_detection:              # Branch 2: 중복 감지
    same_day_same_amount: true
    same_vendor_within_days: 3
  outlier_multiplier: 3.0           # Branch 3: 이상치 배수
```

#### extract.py의 구현

```python
def detect_policy_flags(items: list, policy: dict) -> list:
    limits = policy.get("limits", {})
    outlier_mult = policy.get("outlier_multiplier", 3.0)

    # 카테고리별 평균 계산 (이상치 감지용)
    cat_amounts = defaultdict(list)
    for item in items:
        cat_amounts[item["category_hint"]].append(item["amount"])
    cat_avg = {cat: sum(a)/len(a) for cat, a in cat_amounts.items()}

    # 중복 감지: 동일 날짜 + 동일 금액
    date_amount_map = defaultdict(list)
    for item in items:
        key = (item["date"], item["amount"])
        date_amount_map[key].append(item["id"])
    duplicate_ids = set()
    for key, ids in date_amount_map.items():
        if len(ids) > 1:
            duplicate_ids.update(ids)

    # Decision Tree 적용
    for item in items:
        flags = []

        # Branch 1: Over limit?
        limit = limits.get(item["category_hint"], limits.get("기타", 100000))
        if item["amount"] > limit:
            flags.append("OVER_LIMIT")

        # Branch 2: Duplicate suspect?
        if item["id"] in duplicate_ids:
            flags.append("DUPLICATE_SUSPECT")

        # Branch 3: Outlier?
        avg = cat_avg.get(item["category_hint"], 0)
        if avg > 0 and item["amount"] > avg * outlier_mult:
            flags.append("OUTLIER")

        # Priority: OUTLIER > DUPLICATE > OVER_LIMIT > NONE
        if "OUTLIER" in flags:
            item["policy_flag"] = "OUTLIER"
        elif "DUPLICATE_SUSPECT" in flags:
            item["policy_flag"] = "DUPLICATE_SUSPECT"
        elif "OVER_LIMIT" in flags:
            item["policy_flag"] = "OVER_LIMIT"
        else:
            item["policy_flag"] = "NONE"

        item["all_flags"] = flags

    return items
```

### 설계 원칙

**원칙 1: Script은 "플래그"만, 최종 판단은 LLM**

Decision Tree의 핵심은 **2단계 판단**:

```
Script (Phase 1-2)             LLM (Phase 2)
──────────────────             ──────────────
NONE          ─────────────→   APPROVED
OVER_LIMIT    ─── 합리적? ──→   PENDING (사전승인 필요)
              └── 불충분? ──→   REVIEW (검토 필요)
DUPLICATE     ─── 정상? ────→   APPROVED (왕복 등)
              └── 실제중복? →   FLAG (플래그)
OUTLIER       ─── 설명가능? →   PENDING
              └── 설명불가? →   REVIEW
```

Script이 "이 항목에 문제가 있을 수 있다"고 표시하면, LLM이 맥락을 보고 최종 판단.

```
# BAD: Script이 APPROVED/REJECTED를 직접 판단
if amount <= limit:
    item["status"] = "APPROVED"     # Script이 확정 → LLM 불필요

# GOOD: Script은 플래그만, LLM이 상태를 확정
if amount > limit:
    item["policy_flag"] = "OVER_LIMIT"  # 문제 가능성 표시
# → LLM이 PENDING vs REVIEW를 맥락 보고 판단
```

**원칙 2: 복합 플래그와 우선순위**

하나의 항목에 여러 플래그가 동시 해당될 수 있음:

```python
item["all_flags"] = flags               # 모든 플래그 보존
item["policy_flag"] = primary_flag      # 가장 심각한 것이 대표
```

우선순위: `OUTLIER > DUPLICATE_SUSPECT > OVER_LIMIT > NONE`

이유: 이상치(금액 비정상)가 가장 심각하고, 한도 초과(규정 위반)가 가장 경미.

**원칙 3: 판단 기준은 config에, 로직은 Script에**

```yaml
# config: "무엇을" 기준으로 판단하는가
policy:
  limits:
    식비: 100000            # 숫자만
  outlier_multiplier: 3.0   # 배수만
```

```python
# extract.py: "어떻게" 판단하는가
if amount > limit:          # 비교 로직
    flags.append("OVER_LIMIT")
```

이렇게 분리하면:
- 한도 변경 → config만 수정 (코드 변경 없음)
- 새 플래그 추가 → extract.py에 Branch 추가

### Decision Tree 작성 체크리스트

- [ ] 모든 분기의 종착점이 명확한가? (YES/NO 모두 처리)
- [ ] 복합 플래그의 우선순위를 정의했는가?
- [ ] all_flags로 모든 해당 플래그를 보존하는가?
- [ ] SKILL.md에 ASCII 트리로 시각화했는가?
- [ ] 판단 기준(숫자)은 config, 로직은 Script에 분리했는가?

---

## 5. 패턴 3: Before/After Examples

### 정의

**LLM의 판단 톤, 깊이, 예외 처리 수준을 보정하는 입출력 예시.**

### 왜 Before/After Examples가 필요한가?

Mapping Table과 Decision Tree만으로는 부족한 경우:

```
Script 출력: policy_flag = "DUPLICATE_SUSPECT"

LLM 판단 시 가능한 응답:
  A. "중복입니다. FLAG 처리합니다."                    ← 너무 단순
  B. "같은 날 동일 금액(INV-005)이 있으나,
      '고객사 미팅 이동'과 '사무실 복귀'로
      왕복 이용 확인. 중복 아님."                       ← 적절한 수준
  C. "해당 건은 2025년 1월 20일에 카카오택시에서
      45,000원으로 동일 금액이 청구되었으며..."          ← 너무 장황
```

Before/After Examples는 **B 수준의 응답**을 LLM에게 가르침.

### Invoice Classification의 5가지 예시

각 예시가 서로 다른 **판단 시나리오**를 커버:

| # | 시나리오 | Script 플래그 | LLM 최종 판단 | 핵심 교훈 |
|---|---------|-------------|-------------|----------|
| 1 | 정상 승인 | NONE | APPROVED | 단순 건은 간결하게 |
| 2 | 한도 초과 | OVER_LIMIT | PENDING | 거부가 아닌 사전승인. 1인당 금액 계산 |
| 3 | 중복 의심 | DUPLICATE_SUSPECT | APPROVED | 내역 확인이 핵심. 왕복=정상 |
| 4 | 카테고리 재분류 | OVER_LIMIT | PENDING | Script 힌트가 틀릴 수 있음 |
| 5 | 이상치 | OUTLIER | REVIEW | 자산/비용 구분까지 제시 |

### 예시의 구조

각 예시는 3부분으로 구성:

```markdown
## Example N: {시나리오 제목}

**Before** (Script 추출):
```json
{
  "policy_flag": "OVER_LIMIT",
  ...extracted fields...
}
```

**After** (LLM 판단):
```json
{
  "policy_status": "PENDING",
  "rationale": "판단 근거 텍스트",
  "flag": "조치 사항 또는 null"
}
```

> 포인트: 이 예시에서 LLM이 학습해야 할 핵심
```

### 설계 원칙

**원칙 1: 포인트(교훈)를 명시적으로 기술**

```markdown
# BAD: 예시만 나열
**Before**: ...
**After**: ...

# GOOD: 왜 이렇게 판단했는지 명시
**Before**: ...
**After**: ...
> 포인트: 한도 초과지만 1인당 금액은 합리적 → PENDING(거부가 아님). 맥락 고려.
```

LLM은 `> 포인트:` 라인에서 판단 원칙을 추출.

**원칙 2: 모든 Decision Tree 분기를 예시로 커버**

```
Decision Tree 분기          예시
────────────────           ────
NONE → APPROVED            Example 1 (정상 승인)
OVER_LIMIT → PENDING       Example 2 (한도 초과)
OVER_LIMIT → PENDING       Example 4 (카테고리 재분류 + 사전승인)
DUPLICATE → APPROVED       Example 3 (중복 의심 → 정상)
OUTLIER → REVIEW           Example 5 (이상치)
```

누락된 분기가 있으면 LLM이 해당 상황에서 일관성 없는 판단을 함.

**원칙 3: 경계 사례(Edge Case)를 포함**

```markdown
# Example 3이 경계 사례:
# "동일 날짜 + 동일 금액" = 중복이 맞지만, 내역을 보면 왕복 이용
# → Script의 플래그와 LLM의 최종 판단이 다름

Script: DUPLICATE_SUSPECT
LLM:    APPROVED (내역 분석 결과 정상)
```

이런 경계 사례가 가장 가치 있는 예시. LLM이 "Script을 맹목적으로 따르면 안 된다"는 것을 학습.

**원칙 4: rationale 텍스트의 톤을 예시로 통일**

```json
// Example 1 (단순 건)
"rationale": "팀 미팅 중 음료 구매. 식비 한도(100,000원) 이내. 업무 관련성 명확."

// Example 2 (복잡 건)
"rationale": "식비 건당 한도(100,000원) 4.8배 초과. 단체 회식(8명)으로 1인당 60,000원은 합리적 수준이나 사전승인 필요."
```

공통 패턴:
1. 사실 기술 (무엇이 일어났는가)
2. 한도 대비 비교 (규정과의 관계)
3. 맥락 판단 (왜 이 결론인가)

### Before/After Examples 작성 체크리스트

- [ ] Decision Tree의 모든 분기를 최소 1개 예시로 커버하는가?
- [ ] Script 플래그와 LLM 최종 판단이 다른 경계 사례가 포함되어 있는가?
- [ ] 각 예시에 `> 포인트:` 교훈이 명시되어 있는가?
- [ ] rationale 텍스트의 톤이 예시 간 일관적인가?
- [ ] 예시 수가 3~7개인가? (너무 적으면 커버 부족, 너무 많으면 컨텍스트 낭비)

---

## 6. 패턴 4: Excel Template (Human-Editable)

### 정의

**비기술 사용자가 편집 가능한 Excel 양식을 템플릿으로 사용하여 보고서를 생성.**

### 왜 Excel Template인가?

```
코드 생성 방식 (BAD for non-technical users):
  generate.py가 모든 셀의 서식을 코드로 지정
  → 열 이름 변경 시 코드 수정 필요
  → 재무팀이 양식을 바꿀 수 없음

템플릿 방식 (GOOD):
  재무팀이 template.xlsx를 직접 편집
  → generate.py가 헤더를 동적으로 읽어 적응
  → 서식(색상, 폰트, 테두리)이 자동 보존
```

### Invoice Classification의 구현

#### 3개 핵심 함수

```python
# 1. parse_headers(): 헤더 위치를 동적으로 읽기
def parse_headers(ws, header_row: int) -> dict:
    """Dynamically read column headers → {name: col_index}."""
    headers = {}
    for col in range(1, ws.max_column + 1):
        val = ws.cell(row=header_row, column=col).value
        if val:
            headers[str(val).strip()] = col
    return headers

# 2. copy_cell_style(): 템플릿의 서식을 데이터 셀에 복사
def copy_cell_style(source_cell, target_cell):
    if source_cell.font:
        target_cell.font = copy(source_cell.font)
    if source_cell.fill:
        target_cell.fill = copy(source_cell.fill)
    if source_cell.border:
        target_cell.border = copy(source_cell.border)
    if source_cell.alignment:
        target_cell.alignment = copy(source_cell.alignment)
    if source_cell.number_format:
        target_cell.number_format = source_cell.number_format

# 3. FIELD_MAP: 헤더명 → JSON 필드 매핑
DETAIL_FIELD_MAP = {
    "번호": "id",
    "날짜": "date",
    "거래처": "vendor",
    "내역": "description",
    "금액": "amount",
    "GL코드": "gl_code",
    "카테고리": "category",
    "정책상태": "policy_status",
    "비고": "rationale",
}
```

#### 데이터 쓰기 패턴

```python
for idx, item in enumerate(items):
    row = data_start + idx
    for header_name, col_idx in headers.items():
        field_key = DETAIL_FIELD_MAP.get(header_name)
        if not field_key:
            continue                              # 매핑 없는 열은 건너뜀

        value = item.get(field_key, "")
        cell = ws.cell(row=row, column=col_idx, value=value)

        ref = ws.cell(row=style_ref, column=col_idx)
        copy_cell_style(ref, cell)                # 서식 복사
```

### 사용자 편집 시나리오와 코드 적응

| 사용자 행동 | 코드 적응 방식 |
|-----------|-------------|
| 열 이름 변경 ("정책상태" → "승인여부") | FIELD_MAP에 키 추가 |
| 열 순서 변경 (금액을 앞으로) | parse_headers()가 자동 적응 |
| 열 추가 ("부서" 열) | FIELD_MAP에 매핑 추가 |
| 열 삭제 ("비고" 열) | 매핑 없으면 자동 무시 |
| 서식 변경 (헤더 색상) | copy_cell_style()이 자동 보존 |
| 숫자 형식 변경 (#,##0"원") | number_format 복사로 보존 |

### 다중 시트 설계

```python
SHEET_CONFIG = {
    "summary": {"name": "요약", "data_start": 4, "header_row": 3},
    "detail":  {"name": "상세", "data_start": 4, "header_row": 3},
    "flag":    {"name": "플래그", "data_start": 4, "header_row": 3},
}
```

각 시트마다 별도의 FIELD_MAP과 쓰기 함수:

```python
write_summary_sheet(wb, items, summary)   # 요약 = 카테고리별 집계
write_detail_sheet(wb, items)             # 상세 = 전체 항목
write_flag_sheet(wb, items)               # 플래그 = 검토 필요 항목만
```

### 조건부 서식 (상태별 색상)

```python
STATUS_FILLS = {
    "APPROVED": PatternFill(start_color="C6EFCE", ...),  # 연초록
    "PENDING":  PatternFill(start_color="FFEB9C", ...),  # 연노랑
    "FLAG":     PatternFill(start_color="FFC7CE", ...),  # 연빨강
    "REVIEW":   PatternFill(start_color="E6B8AF", ...),  # 연분홍
}

# 상태 셀에 색상 적용
if field_key == "policy_status":
    original_status = item.get("policy_status", "")
    fill = STATUS_FILLS.get(original_status)
    if fill:
        cell.fill = fill
```

### Excel Template 작성 체크리스트

- [ ] `parse_headers()`로 동적 헤더 읽기를 구현했는가?
- [ ] `copy_cell_style()`로 5가지 서식(font, fill, border, alignment, number_format)을 복사하는가?
- [ ] FIELD_MAP으로 헤더명 → JSON 키를 매핑했는가?
- [ ] 매핑 없는 헤더는 에러 없이 무시하는가?
- [ ] 다중 시트의 경우 SHEET_CONFIG로 시트별 설정을 분리했는가?
- [ ] `data_start` 행의 셀을 `style_ref`로 사용하여 서식을 복사하는가?

---

## 7. 4패턴 통합 설계

### Invoice Classification의 전체 파이프라인

```
Phase 1-1: convert.py
┌─────────────────────────────────────────────┐
│  CSV → JSON 변환 (기계적)                     │
│  expenses.csv → raw_data.json               │
└──────────────────────┬──────────────────────┘
                       │
Phase 1-2: extract.py  │
┌──────────────────────▼──────────────────────┐
│  ★ Mapping Table                            │
│    vendor+description → category_hint       │
│    "스타벅스 강남역점"+"팀 미팅 커피"            │
│    → keywords["커피"] → 식비, GL-5300         │
│                                             │
│  ★ Decision Tree                            │
│    policy flags: NONE/OVER_LIMIT/            │
│    DUPLICATE_SUSPECT/OUTLIER                 │
│                                             │
│  → extracted_data.json (hints + flags)      │
└──────────────────────┬──────────────────────┘
                       │
Phase 2: LLM Judgment  │
┌──────────────────────▼──────────────────────┐
│  ★ Before/After Examples 참조                │
│                                             │
│  1. category_hint 검증/재분류                 │
│     "기타" → "교육비" (교보문고+업무참고도서)    │
│                                             │
│  2. policy_flag → policy_status 확정          │
│     DUPLICATE_SUSPECT → APPROVED (왕복 확인)  │
│     OVER_LIMIT → PENDING (회식 사전승인)       │
│                                             │
│  3. rationale + flag 텍스트 생성              │
│  4. summary 집계                             │
│                                             │
│  → judged_data.json (확정 결과)               │
└──────────────────────┬──────────────────────┘
                       │
Phase 3: generate.py   │
┌──────────────────────▼──────────────────────┐
│  ★ Excel Template                           │
│    template.xlsx 로드                        │
│    → parse_headers() 동적 읽기               │
│    → copy_cell_style() 서식 보존             │
│    → 3시트 채우기 (요약/상세/플래그)            │
│                                             │
│  → expense_report.xlsx + expense_report.json │
└─────────────────────────────────────────────┘
```

### 패턴 간 데이터 흐름

```
                    config/settings.yaml
                    ┌───────────────────┐
                    │ ★ Mapping Table   │──→ extract.py (Phase 1-2)
                    │   gl_accounts     │
                    │                   │
                    │ ★ Decision Tree   │──→ extract.py (Phase 1-2)
                    │   policy.limits   │
                    │   policy.outlier  │
                    └───────────────────┘

                    references/examples.md
                    ┌───────────────────┐
                    │ ★ Before/After    │──→ LLM (Phase 2)
                    │   5 scenarios     │    preset-prompt.md에서 참조 지시
                    └───────────────────┘

                    templates/template.xlsx
                    ┌───────────────────┐
                    │ ★ Excel Template  │──→ generate.py (Phase 3)
                    │   3 sheets        │
                    └───────────────────┘
```

### 파일 구조 전체

```
invoice-classification/
├── SKILL.md                       # 4패턴 문서화 (★ 마커)
├── config/
│   └── settings.yaml              # ★ Mapping Table + ★ Decision Tree 기준
├── references/
│   ├── schemas.md                 # 데이터 스키마 (3개)
│   └── examples.md                # ★ Before/After Examples (5건)
├── scripts/
│   ├── convert.py                 # Phase 1-1: CSV/XLSX → JSON
│   ├── extract.py                 # Phase 1-2: ★ Mapping + ★ Decision Tree
│   └── generate.py                # Phase 3: ★ Excel Template → 보고서
├── templates/
│   └── template.xlsx              # ★ 사용자 편집 가능한 Excel 템플릿
├── sample/
│   └── expenses.csv               # 테스트 데이터 (12건)
└── preset-prompt.md               # AIP: LLM에게 ★ B/A Examples 참조 지시
```

---

## 8. config 설계: 패턴별 영역 분리

### config/settings.yaml의 3개 영역

```yaml
# =================================================================
# 영역 1: ★ Mapping Table — extract.py가 사용
# =================================================================
gl_accounts:
  교통비:
    code: "GL-5100"
    keywords: [택시, KTX, 기차, ...]
  식비:
    code: "GL-5300"
    keywords: [식사, 회식, 점심, ...]
  # ... (7개 카테고리)

# =================================================================
# 영역 2: ★ Decision Tree 기준 — extract.py가 사용
# =================================================================
policy:
  limits:                          # Branch 1 기준
    교통비: 200000
    식비: 100000
    # ...
  duplicate_detection:             # Branch 2 기준
    same_day_same_amount: true
  outlier_multiplier: 3.0          # Branch 3 기준

# =================================================================
# 영역 3: 추출 설정 — convert.py/extract.py가 사용
# =================================================================
extraction:
  date_format: "%Y-%m-%d"
  vendor_column: "거래처"
  description_column: "내역"
  amount_column: "금액"
```

### 다른 패턴은 왜 config에 없는가?

| 패턴 | config에 있는가? | 이유 |
|------|-----------------|------|
| Mapping Table | O | Script이 키워드 룩업에 사용 |
| Decision Tree | O | Script이 수치 기준으로 비교에 사용 |
| Before/After Examples | X | LLM이 자연어로 읽음 → references/ |
| Excel Template | X | 바이너리 파일 → templates/ |

**원칙: config에는 Script이 프로그래밍적으로 사용하는 데이터만.**

---

## 9. extract.py: Mapping + Decision Tree 구현

### 스크립트의 2단계 파이프라인

```python
def main():
    # ...
    items = data["items"]

    # Step 1: ★ Mapping Table → category + GL code hints
    for item in items:
        cat, gl_code = match_category(
            item["vendor"], item["description"], gl_accounts
        )
        item["category_hint"] = cat
        item["gl_code_hint"] = gl_code

    # Step 2: ★ Decision Tree → policy flags
    items = detect_policy_flags(items, policy)
```

### 출력 예시

```json
{
  "id": "INV-003",
  "date": "2025-01-18",
  "vendor": "한우마을",
  "description": "부서 신년회 회식 (8명)",
  "amount": 480000,
  "category_hint": "식비",          // ← Mapping Table 결과
  "gl_code_hint": "GL-5300",       // ← Mapping Table 결과
  "policy_flag": "OVER_LIMIT",     // ← Decision Tree 결과
  "all_flags": ["OVER_LIMIT"]      // ← 모든 해당 플래그
}
```

### hint vs 확정의 데이터 흐름

```
extract.py 출력               LLM 판단 후
─────────────                ──────────
category_hint: "식비"   →    category: "식비"       (동일)
category_hint: "기타"   →    category: "교육비"     (재분류!)
gl_code_hint: "GL-5900" →    gl_code: "GL-5500"    (재분류!)
policy_flag: "OVER_LIMIT" →  policy_status: "PENDING"  (확정)
policy_flag: "DUPLICATE"  →  policy_status: "APPROVED" (뒤집힘!)
```

---

## 10. generate.py: Excel Template 구현

### 핵심 패턴: Template → Load → Parse → Write → Save

```python
def main():
    # 1. LLM 판단 결과 로드
    with open(judged_path) as f:
        data = json.load(f)

    # 2. Excel Template 로드
    wb = load_template(config)       # templates/template.xlsx

    # 3. 시트별 쓰기
    write_summary_sheet(wb, items, summary)   # 요약
    write_detail_sheet(wb, items)             # 상세
    write_flag_sheet(wb, items)               # 플래그

    # 4. 저장
    wb.save(xlsx_path)
```

### 시트별 쓰기 로직

**상세 시트 (전체 항목)**:

```python
def write_detail_sheet(wb, items):
    ws = wb["상세"]
    headers = parse_headers(ws, header_row=3)    # 동적 헤더 읽기

    for idx, item in enumerate(items):
        row = data_start + idx
        for header_name, col_idx in headers.items():
            field_key = DETAIL_FIELD_MAP.get(header_name)
            if not field_key:
                continue                          # 매핑 없는 열 무시

            value = item.get(field_key, "")
            cell = ws.cell(row=row, column=col_idx, value=value)

            ref = ws.cell(row=style_ref, column=col_idx)
            copy_cell_style(ref, cell)            # 서식 복사
```

**플래그 시트 (검토 필요 항목만)**:

```python
def write_flag_sheet(wb, items):
    flagged = [i for i in items
               if i.get("policy_status") in ("PENDING", "FLAG", "REVIEW")]
    # flagged만 쓰기 (같은 패턴)
```

### 상태별 색상 적용

```python
# 정책 상태 셀에 배경색 적용
if field_key == "policy_status":
    original_status = item.get("policy_status", "")
    fill = STATUS_FILLS.get(original_status)
    if fill:
        cell.fill = fill
```

결과:
- 승인 → 연초록 배경
- 승인대기 → 연노랑 배경
- 플래그 → 연빨강 배경
- 검토필요 → 연분홍 배경

---

## 11. preset-prompt.md: LLM에게 패턴 위임

### Invoice Classification의 preset-prompt.md

```markdown
## 역할
당신은 경비 심사 전문가입니다.

## 참조 자료
- `config/settings.yaml`: GL 계정 매핑 테이블, 정책 한도
- `references/examples.md`: Before/After 판단 예시 5건    ← ★ 핵심

## 수행 작업
### 1. 카테고리 및 GL코드 확정
- Script의 `category_hint`를 검증. 부정확하면 재분류.

### 2. 정책 상태 확정 (Decision Tree 적용)
- `policy_flag`에 따라 최종 상태 결정:
  - `NONE` → `APPROVED`
  - `OVER_LIMIT` → `PENDING` 또는 `REVIEW`
  - `DUPLICATE_SUSPECT` → `APPROVED` 또는 `FLAG`
  - `OUTLIER` → `PENDING` 또는 `REVIEW`

### 3. 판단 근거 및 플래그
- `references/examples.md`의 Before/After 예시를 참고하여 판단 톤 맞춤.
```

### 핵심: preset-prompt.md에서 Before/After Examples를 참조시킴

```
preset-prompt.md        references/examples.md
┌──────────────┐        ┌────────────────────┐
│ "참조 자료:   │  ──→   │ Example 1~5        │
│  examples.md" │        │ Before/After pairs │
└──────────────┘        └────────────────────┘
```

LLM은 preset-prompt.md의 지시에 따라 examples.md를 읽고 판단 톤을 맞춤.

### LLM에게 위임하는 것 vs 안 하는 것

| 항목 | LLM에게 위임 | 이유 |
|------|------------|------|
| category_hint → category 확정 | O | vendor+description 의미 이해 필요 |
| policy_flag → policy_status 확정 | O | 맥락 판단 필요 (왕복=정상) |
| rationale 텍스트 생성 | O | 자연어 생성 |
| summary.overall_assessment | O | 종합 평가는 LLM이 적합 |
| by_category 집계 | O | LLM이 JSON 내에서 계산 가능 |
| Excel 생성 | X | 기계적 작업 → generate.py |
| 키워드 매칭 | X | 정확한 룩업 → extract.py |

---

## 12. 판단 패턴 선택 가이드

### 새 Skill을 만들 때 어떤 패턴을 사용할지

```
질문 1: 입력을 카테고리로 분류해야 하는가?
  └─ YES → ★ Mapping Table
  └─ NO  → 다음

질문 2: 조건 분기로 이상/정상을 판단해야 하는가?
  └─ YES → ★ Decision Tree
  └─ NO  → 다음

질문 3: LLM의 판단 품질이 예시에 따라 크게 달라지는가?
  └─ YES → ★ Before/After Examples
  └─ NO  → 다음

질문 4: 비기술 사용자가 출력 양식을 편집해야 하는가?
  └─ YES → ★ Excel Template
  └─ NO  → Jinja2 Template 또는 코드 생성
```

### 패턴 조합 예시

| 유즈케이스 | Mapping | Decision | B/A | Excel |
|-----------|---------|----------|-----|-------|
| 경비 분류 보고서 | O | O | O | O |
| 회의록 정리 | - | - | O | - |
| 품질 검사 보고서 | O | O | O | - |
| 성적 처리 | - | O | - | O |
| 이력서 스크리닝 | O | O | O | - |
| 재고 발주 | O | O | - | O |

### 패턴별 적합 상황

**Mapping Table**: 입력 키워드 → 카테고리 분류가 필요할 때
- 예: 거래처명 → GL 계정, 이메일 제목 → 부서, 증상 → 진단 코드

**Decision Tree**: 수치/규칙 기반 이상 감지가 필요할 때
- 예: 금액 > 한도, 기간 > N일, 재고 < 안전재고

**Before/After Examples**: LLM 판단의 톤/깊이/예외 처리를 보정할 때
- 예: 경비 승인/거부 근거, 코드 리뷰 피드백, 채용 평가 코멘트

**Excel Template**: 재무/인사/품질 부서가 양식을 직접 관리할 때
- 예: 경비 보고서, 성적표, 검사 보고서, 재고 현황표

---

## 13. 체크리스트

### Mapping Table
- [ ] config에 카테고리별 키워드 목록이 있는가?
- [ ] Fallback 카테고리("기타")가 정의되어 있는가?
- [ ] Script 결과가 `_hint` 접미사로 저장되어 LLM 재분류가 가능한가?
- [ ] vendor + description을 결합하여 매칭하는가?

### Decision Tree
- [ ] SKILL.md에 ASCII 트리로 시각화되어 있는가?
- [ ] 수치 기준(한도, 배수)이 config에 분리되어 있는가?
- [ ] Script은 플래그만 생성하고, 최종 판단은 LLM에게 위임하는가?
- [ ] 복합 플래그의 우선순위가 정의되어 있는가?
- [ ] `all_flags`로 모든 해당 플래그를 보존하는가?

### Before/After Examples
- [ ] Decision Tree의 모든 분기를 예시로 커버하는가?
- [ ] Script 플래그 ≠ LLM 최종 판단인 경계 사례가 포함되어 있는가?
- [ ] 각 예시에 `> 포인트:` 교훈이 명시되어 있는가?
- [ ] rationale 텍스트의 톤이 예시 간 일관적인가?
- [ ] 예시 수가 3~7개인가?

### Excel Template
- [ ] `parse_headers()`로 동적 헤더 읽기를 구현했는가?
- [ ] `copy_cell_style()`로 5가지 서식을 복사하는가?
- [ ] FIELD_MAP으로 헤더명 → JSON 키를 매핑했는가?
- [ ] 매핑 없는 헤더는 에러 없이 무시하는가?
- [ ] 비기술 사용자가 열 이름/순서/서식을 바꿔도 코드가 적응하는가?

### 통합
- [ ] config에 Mapping Table 영역과 Decision Tree 영역이 구분되어 있는가?
- [ ] Before/After Examples가 references/ 에 있는가? (config X)
- [ ] preset-prompt.md에서 examples.md 참조를 명시했는가?
- [ ] SKILL.md에 ★ 마커로 각 패턴의 위치가 표시되어 있는가?
- [ ] 파이프라인의 각 Phase가 어떤 패턴을 담당하는지 명확한가?

---

*이 교육 자료는 Invoice Classification Skill의 실제 코드와 문서를 기반으로 작성되었습니다.*
*기본편: `skill-authoring-guide.md` (T-Connect 기반)*
