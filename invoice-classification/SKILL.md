---
name: invoice-classification
display_name: "송장 분류 & 경비보고서"
description: "경비 항목을 GL 계정으로 분류하고, 정책 준수 여부를 판단하여 Excel 경비보고서를 생성합니다."
tier: full
language: python
tags: [finance, invoice, expense-report, excel-template, mapping-table, decision-tree, config-driven, 3-phase-pipeline]
input: "CSV/XLSX 경비 데이터 (날짜, 거래처, 내역, 금액)"
output: "Excel 경비보고서 (요약 + 상세 + 플래그) + JSON"
---

# 송장 분류 & 경비보고서

## 파이프라인 구조

```
[CSV/XLSX 경비 데이터]
        │
   Phase 1-1: convert.py (Script)
   │  CSV/XLSX → JSON 변환
        │
   Phase 1-2: extract.py (Script)
   │  ★ Mapping Table: 키워드 → 카테고리 + GL코드
   │  ★ Decision Tree: 정책 위반 플래그 (한도초과/중복/이상치)
        │
   Phase 2: LLM Judgment
   │  ★ Before/After Examples 기반 판단 보정
   │  카테고리 재분류, 정책 상태 확정, 근거 제시
        │
   Phase 3: generate.py (Script)
   │  ★ Excel Template: template.xlsx 로드 → 헤더 동적 읽기 → 데이터 채우기
        │
[Excel 경비보고서 + JSON]
```

## 역할 분리

### Script (결정적)
- CSV/XLSX 파싱 및 변환
- **Mapping Table**: config의 gl_accounts 키워드 → 카테고리 + GL코드 매칭
- **Decision Tree**: 한도 초과 / 중복 의심 / 이상치 플래그 분류
- **Excel Template**: 서식 보존하며 3시트 보고서 생성

### LLM (판단)
- Script의 카테고리 힌트 검증 및 재분류
- 정책 상태 최종 확정 (APPROVED/PENDING/FLAG/REVIEW)
- 중복 의심 건의 실제 중복 여부 판단 (내역 분석)
- 판단 근거(rationale) 및 조치(flag) 텍스트 생성

## ★ Decision Tree

```
경비 항목
├─ 금액 > 카테고리별 한도?
│  └─ YES → OVER_LIMIT
├─ 동일 날짜 + 동일 금액 존재?
│  └─ YES → DUPLICATE_SUSPECT
├─ 카테고리 평균 × 3배 초과?
│  └─ YES → OUTLIER
└─ 해당 없음 → NONE

LLM 최종 판단:
├─ NONE → APPROVED (승인)
├─ OVER_LIMIT
│  ├─ 합리적 사유 있음 → PENDING (승인대기)
│  └─ 사유 불충분 → REVIEW (검토필요)
├─ DUPLICATE_SUSPECT
│  ├─ 내역 확인 시 정상 → APPROVED
│  └─ 실제 중복 → FLAG (플래그)
└─ OUTLIER
   ├─ 합리적 설명 가능 → PENDING
   └─ 설명 불가 → REVIEW
```

## ★ Mapping Table (config/settings.yaml)

```yaml
gl_accounts:
  교통비:
    code: "GL-5100"
    keywords: [택시, KTX, 기차, 버스, 항공, 주차]
  식비:
    code: "GL-5300"
    keywords: [식사, 회식, 점심, 커피, 카페]
  소프트웨어:
    code: "GL-5200"
    keywords: [구독, 라이선스, SaaS, AWS, Adobe]
  ...
```

## ★ Before/After Examples (references/examples.md)

5가지 판단 패턴:
1. **정상 승인**: 한도 내 + 업무 관련 명확 → APPROVED
2. **한도 초과**: 단체 회식 등 합리적 사유 → PENDING (거부가 아님)
3. **중복 의심**: 동일 날짜+금액이나 왕복 이용 → APPROVED (내역 확인 필수)
4. **카테고리 재분류**: Script 힌트 부정확 → LLM이 vendor+description으로 재분류
5. **이상치**: 큰 금액 + 모호한 내역 → REVIEW (자산/비용 구분 검토)

## ★ Excel Template (templates/template.xlsx)

### 핵심 원리
> **템플릿은 재무팀 직원이 편집 가능**

| 시트 | 용도 | 헤더 |
|------|------|------|
| 요약 | 카테고리별 합계 + 상태별 건수 | 카테고리, GL코드, 건수, 합계, 비율 |
| 상세 | 전체 경비 항목 | 번호, 날짜, 거래처, 내역, 금액, GL코드, 카테고리, 정책상태, 비고 |
| 플래그 | 검토 필요 항목 | 번호, 날짜, 거래처, 내역, 금액, 상태, 사유, 조치 |

### 사용자 편집 시나리오
- 열 이름 변경: "정책상태" → "승인여부" (generate.py가 자동 적응)
- 열 추가: "부서" 열 추가 → generate.py의 FIELD_MAP에 매핑 추가
- 서식 변경: 헤더 색상, 금액 표시 형식 → 출력에 그대로 반영

## 파일 구조

```
invoice-classification/
├── SKILL.md
├── config/settings.yaml              # ★ Mapping Table + Decision Tree 기준
├── references/
│   ├── schemas.md                     # 데이터 스키마
│   └── examples.md                    # ★ Before/After Examples (5건)
├── scripts/
│   ├── convert.py                     # Phase 1-1: CSV/XLSX → JSON
│   ├── extract.py                     # Phase 1-2: 매핑 + 플래그
│   └── generate.py                    # Phase 3: ★ Excel Template → 보고서
├── templates/
│   └── template.xlsx                  # ★ 사용자 편집 가능한 Excel 템플릿
├── sample/
│   └── expenses.csv                   # 테스트 데이터 (12건)
└── preset-prompt.md                   # AIP Phase 2 프롬프트
```
