# Quality Inspection - Before/After 판단 예시

LLM이 Phase 2에서 참조해야 하는 판단 기준 예시입니다.
각 예시는 raw_data.json의 항목(Before)과 기대되는 judged_data.json 결과(After)를 보여줍니다.

---

## 예시 1: PASS (명확한 합격)

### Before (raw_data)
```json
{
  "part_id": "SUS-001",
  "part_name": "서스펜션 스프링",
  "category": "mechanical",
  "measurement_type": "spring_rate",
  "measured_value": 30.0,
  "unit": "N/mm",
  "spec_min": 25.0,
  "spec_max": 35.0,
  "critical": false,
  "margin_pct": 50.0,
  "initial_class": "PASS"
}
```

### After (LLM 판단)
```json
{
  "final_result": "PASS",
  "rationale": "스프링 상수(30.0 N/mm)가 규격 중앙값(30.0)에 정확히 위치. 충분한 마진(50%) 확보.",
  "defect_code": null,
  "corrective_action": null,
  "priority": null
}
```

**포인트**: PASS 항목은 간결하게 처리. 불필요한 분석 없이 합격 확인만.

---

## 예시 2: BORDERLINE → CONDITIONAL PASS (비안전 부품, 관련 측정 정상)

### Before (raw_data)
```json
{
  "part_id": "ENG-001",
  "part_name": "엔진 마운트 볼트",
  "category": "mechanical",
  "measurement_type": "torque",
  "measured_value": 49.2,
  "unit": "Nm",
  "spec_min": 40.0,
  "spec_max": 50.0,
  "critical": false,
  "margin_pct": 8.0,
  "initial_class": "BORDERLINE"
}
```

**동일 부품 관련 측정**:
```json
{
  "part_id": "ENG-001",
  "measurement_type": "temperature",
  "measured_value": 82.5,
  "spec_max": 85.0,
  "margin_pct": 2.9,
  "initial_class": "BORDERLINE"
}
```

### After (LLM 판단)
```json
{
  "final_result": "FAIL",
  "rationale": "토크(49.2Nm, 마진 8%)와 온도(82.5°C, 마진 2.9%) 모두 경계값. 동일 부품의 두 측정이 동시에 상한 근처에 위치하여 공정 제어 이탈 가능성. 비안전 부품이나 복합 경계 상황이므로 불합격 처리.",
  "defect_code": "PRC",
  "corrective_action": "토크 렌치 캘리브레이션 확인, 체결 공정 파라미터 검토, 해당 라인 5개 샘플 추가 검사",
  "priority": "medium"
}
```

**포인트**: 개별적으로는 BORDERLINE이지만, **동일 부품의 복수 항목이 동시에 경계**이면 시스템 이슈로 판단.

---

## 예시 3: BORDERLINE → FAIL (안전 부품)

### Before (raw_data)
```json
{
  "part_id": "BRK-001",
  "part_name": "브레이크 패드",
  "category": "safety",
  "measurement_type": "friction_coefficient",
  "measured_value": 0.31,
  "unit": "",
  "spec_min": 0.3,
  "spec_max": 0.5,
  "critical": true,
  "margin_pct": 5.0,
  "initial_class": "BORDERLINE"
}
```

### After (LLM 판단)
```json
{
  "final_result": "FAIL",
  "rationale": "마찰계수(0.31)가 하한(0.3) 근처(마진 5%). 안전 부품(브레이크)이므로 Decision Tree에 따라 경계값 불허. 제동 성능 저하 위험.",
  "defect_code": "CRT",
  "corrective_action": "해당 로트 전수 검사, 패드 소재 마찰 특성 재시험, 공급업체 시정 요청서 발행",
  "priority": "critical"
}
```

**포인트**: `critical=true`인 안전 부품은 BORDERLINE이어도 **무조건 FAIL**. Decision Tree의 "안전 부품은 경계값 불허" 규칙 적용.

---

## 예시 4: FAIL → 근본 원인 분류 (electrical)

### Before (raw_data)
```json
{
  "part_id": "WIR-001",
  "part_name": "메인 배선 하네스",
  "category": "electrical",
  "measurement_type": "resistance",
  "measured_value": 1.5,
  "unit": "Ω",
  "spec_min": null,
  "spec_max": 1.0,
  "critical": false,
  "margin_pct": -50.0,
  "initial_class": "FAIL"
}
```

### After (LLM 판단)
```json
{
  "final_result": "FAIL",
  "rationale": "저항값(1.5Ω)이 상한(1.0Ω)을 50% 초과. 접촉 저항 증가 또는 도체 단면적 부족이 의심됨.",
  "defect_code": "SOL",
  "corrective_action": "커넥터 납땜 상태 육안 검사, 재납땜 후 재측정, 동일 생산 라인 배선 5개 샘플링",
  "priority": "high"
}
```

**포인트**: electrical 카테고리의 저항 이상 → **SOL (납땜 불량)** 매핑. 결함 코드는 config/settings.yaml의 Mapping Table에서 카테고리별 적합한 코드를 선택.

---

## 예시 5: FAIL → 시스템 이슈 탐지

### Before (raw_data - 동일 부품 복수 FAIL)
```json
[
  {"part_id": "ECU-001", "measurement_type": "voltage", "measured_value": 4.5, "spec_min": 4.75, "initial_class": "FAIL"},
  {"part_id": "ECU-001", "measurement_type": "current", "measured_value": 3.5, "spec_max": 3.0, "initial_class": "FAIL"}
]
```

### After (LLM 판단 - system_issues에 추가)
```json
{
  "system_issues": [
    {
      "description": "ECU-001(엔진 제어 유닛)의 전압과 전류가 동시에 규격 이탈. 전원 공급 계통 또는 ECU 자체 결함 의심.",
      "affected_parts": ["ECU-001"],
      "suggested_investigation": "ECU 전원 입력부 점검, 레귤레이터 출력 확인, 해당 배치 ECU 전수 전기 검사"
    }
  ]
}
```

**포인트**: 동일 부품의 **복수 측정이 동시 FAIL**이면 개별 원인이 아닌 **시스템 레벨 이슈**로 판단.
