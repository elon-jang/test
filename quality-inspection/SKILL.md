---
name: quality-inspection
display_name: "제조 품질 검사 보고서"
description: "부품 측정 데이터와 사양 기준을 비교하여 합격/불합격을 판정하고, 경계값은 LLM이 맥락 기반으로 판단하여 품질 보고서를 생성합니다."
version: "1.0.0"
author: "elon"
tier: full
language: python
tags:
  - quality-inspection
  - manufacturing
  - data-pipeline
  - llm-judgment
  - config-driven
---

# 제조 품질 검사 보고서 스킬

## 개요

부품 검사 측정 데이터와 사양 기준서를 입력받아, 규격 대비 합격/불합격을 자동 판정합니다.
경계값(규격 한계 근처)은 LLM이 관련 측정값, 부품 특성, 안전 등급을 종합하여 판단합니다.

## 역할 분배 원칙

| 담당 | 역할 | 설명 |
|------|------|------|
| **Script** | 결정적 처리 | CSV/Excel 파싱, 규격 대비 수치 비교, 마진 계산, 보고서 포맷 생성 |
| **LLM** | 판단·추론 | 경계값 최종 판정, 근본 원인 분류, 시정 조치 우선순위, 시스템 이슈 탐지 |

## Input

| 파일 | 형식 | 설명 |
|------|------|------|
| 검사 측정 데이터 (Measurements) | `.csv` / `.xlsx` | 부품별 측정값 (part_id, type, value, unit) |
| 사양 기준서 (Specifications) | `.csv` / `.xlsx` | 부품별 규격 범위 (spec_min, spec_max, critical) |

## Output

| 파일 | 형식 | 설명 |
|------|------|------|
| `inspection_report.json` | JSON | 구조화된 품질 검사 보고서 |
| `inspection_report.md` | Markdown | 사람이 읽기 쉬운 보고서 |

## Execution Flow

```
[measurements.csv] + [specifications.csv]
       │
       ▼
┌─────────────────────────┐
│ Phase 1-1: convert      │  Script (convert.py)
│ XLSX → CSV 정규화        │  CSV는 그대로, XLSX는 변환
└──────────┬──────────────┘
           │  converted/*.csv
           ▼
┌─────────────────────────┐
│ Phase 1-2: extract      │  Script (extract.py)
│ 규격 대비 비교 + 분류    │  config/settings.yaml 기반
│ PASS / BORDERLINE / FAIL │  마진 계산, 초기 분류
└──────────┬──────────────┘
           │  raw_data.json
           ▼
┌─────────────────────────┐
│ Phase 2: judgment       │  ★ LLM
│ 경계값 최종 판정         │  Decision Tree 적용
│ 근본 원인 분류           │  Mapping Table 참조
│ 시정 조치 추천           │  Before/After 예시 참조
└──────────┬──────────────┘
           │  judged_data.json
           ▼
┌─────────────────────────┐
│ Phase 3: generate       │  Script (generate.py)
│ 품질 보고서 생성         │  JSON + Markdown 출력
└──────────┬──────────────┘
           │
           ▼
[inspection_report.json / .md]
```

---

## Phase 2: LLM Judgment 상세

### ★ Decision Tree (판정 흐름도)

LLM은 `raw_data.json`의 각 측정 항목에 대해 아래 의사결정 트리를 따릅니다.

```
측정값 vs 규격
│
├─ 규격 범위 내 (margin > 10%) ──────────────────→ ✅ PASS
│
├─ 규격 범위 내 (margin ≤ 10%) ──→ ⚠️ BORDERLINE
│   │
│   ├─ 안전 부품 (critical=true)?
│   │   ├─ YES → ❌ FAIL (안전 부품은 경계값 불허)
│   │   └─ NO  → 관련 측정값 확인
│   │       ├─ 동일 부품 다른 측정 모두 정상 → ✅ CONDITIONAL PASS
│   │       ├─ 동일 부품 다른 측정도 경계   → ❌ FAIL + 시스템 이슈 플래그
│   │       └─ 관련 측정 없음              → ✅ CONDITIONAL PASS (재검사 권고)
│
└─ 규격 범위 밖 ──────────────────→ ❌ FAIL
    │
    └─ 근본 원인 분류 (★ Mapping Table 참조)
        ├─ MAT: 재료 불량 (원자재 성적서 이상, 로트 불량)
        ├─ PRC: 공정 이상 (공정 파라미터 이탈, 온도/압력 이상)
        ├─ TLG: 금형/치공구 (마모, 파손, 교체 주기 초과)
        ├─ HUM: 작업자 오류 (세팅 미스, 절차 미준수)
        ├─ SOL: 납땜 불량 (electrical 카테고리)
        ├─ CMP: 부품 불량 (electrical 카테고리)
        ├─ ESD: 정전기 손상 (electrical 카테고리)
        ├─ CAL: 캘리브레이션 오류 (electrical 카테고리)
        └─ CRT: 치명적 결함 (safety 카테고리)
```

### ★ Mapping Table (결함 코드 매핑)

`config/settings.yaml`의 `defect_codes` 섹션을 참조합니다.

| 카테고리 | 코드 | 설명 | 판단 기준 |
|---------|------|------|----------|
| mechanical | MAT | 재료 불량 | 측정값이 소재 물성(강도, 경도, 탄성)과 관련된 항목에서 이탈 |
| mechanical | PRC | 공정 이상 | 가공 치수, 토크, 온도 등 공정 제어 항목에서 이탈 |
| mechanical | TLG | 금형/치공구 마모 | 반복 불량, 점진적 이탈 패턴, 치수 편차 증가 |
| mechanical | HUM | 작업자 오류 | 단발성 이탈, 세팅값 오류, 절차 스킵 |
| electrical | SOL | 납땜 불량 | 저항 이상, 접촉 불량 패턴 |
| electrical | CMP | 부품 불량 | 전압/전류 이상, 부품 자체 규격 미달 |
| electrical | ESD | 정전기 손상 | 간헐적 오동작, 특정 조건에서만 이탈 |
| electrical | CAL | 캘리브레이션 오류 | 센서 응답 시간, 측정 편차, 일관된 오프셋 |
| safety | CRT | 치명적 결함 | 안전 부품 규격 미달, 즉시 사용 중지 필요 |

### ★ Before/After 예시

LLM 판단의 기대 수준을 보여주는 참고 예시입니다. `references/examples.md`에 상세 버전이 있습니다.

#### 예시 1: BORDERLINE → CONDITIONAL PASS (비안전 부품)

**Before** (raw_data에서):
```
part: ENG-001 (엔진 마운트 볼트, mechanical)
measurement: torque = 49.2 Nm
spec: 40~50 Nm → margin_pct: 1.6% (상한 근처)
initial_class: BORDERLINE
critical: false
```

**After** (LLM 판단):
```
result: CONDITIONAL PASS
rationale: "토크 값이 상한 근처(49.2/50)이나, 동일 부품의 온도 측정(82.5°C/85°C)이
           정상 범위 내. 기계 부품(비안전)이므로 조건부 합격. 다음 로트 재확인 권장."
defect_code: null
corrective_action: "다음 로트 검사 시 토크 측정 포인트 추가 확인"
priority: low
```

#### 예시 2: BORDERLINE → FAIL (안전 부품)

**Before**:
```
part: BRK-001 (브레이크 패드, safety)
measurement: friction_coefficient = 0.31
spec: 0.3~0.5 → margin_pct: 1.5% (하한 근처)
initial_class: BORDERLINE
critical: true
```

**After**:
```
result: FAIL
rationale: "마찰계수(0.31)가 하한(0.3) 근처. 안전 부품(브레이크)이므로 경계값 불허.
           제동 성능 저하 위험이 있어 불합격 처리."
defect_code: CRT (치명적 결함)
corrective_action: "해당 로트 전수 검사, 패드 소재 마찰 특성 재시험, 공급업체 시정 요청"
priority: critical
```

#### 예시 3: FAIL → 근본 원인 분류

**Before**:
```
part: WIR-001 (메인 배선 하네스, electrical)
measurement: resistance = 1.5 Ω
spec: ~1.0 Ω → margin_pct: -50% (상한 초과)
initial_class: FAIL
critical: false
```

**After**:
```
result: FAIL
rationale: "저항값(1.5Ω)이 상한(1.0Ω)을 50% 초과. 접촉 저항 증가 또는 도체 단면적
           부족이 의심됨. 납땜 품질 확인 필요."
defect_code: SOL (납땜 불량)
corrective_action: "커넥터 납땜 상태 육안 검사, 재납땜 후 재측정, 동일 라인 샘플링 검사"
priority: high
```

---

## Phase별 CLI

### Phase 1-1: convert.py
```bash
python scripts/convert.py \
  --measurements sample/measurements.csv \
  --specifications sample/specifications.csv \
  --output-dir work/converted
```

### Phase 1-2: extract.py
```bash
python scripts/extract.py \
  --measurements work/converted/measurements.csv \
  --specifications work/converted/specifications.csv \
  --output work/raw_data.json
```

### Phase 3: generate.py
```bash
python scripts/generate.py \
  --judged-data work/judged_data.json \
  --output-dir output
```
