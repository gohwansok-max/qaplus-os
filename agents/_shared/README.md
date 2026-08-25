# Shared Brain — 9명 임원 공통 두뇌

이 폴더는 김이사(CSO) + 8명 C-level이 공유하는 **사고 운영체제**입니다.

## 파일

- `cognitive-core.md` — 9명 공통 사고 엔진 (메타인지, 제1원칙, 4대 사고도구, 독립적 판단, Cross-Lens, Inversion, 보고 템플릿)

## 작동 방식

각 임원의 `agents/{직책}/README.md` 상단에 다음 줄이 있습니다:

```
@include ../_shared/cognitive-core.md
```

→ Claude가 임원 페르소나를 로드할 때 cognitive-core가 함께 로드됩니다.
→ 이 파일 1개를 수정하면 9명 전원이 동시에 업그레이드됩니다.

## 수강생 활용

본인 사업에 맞게 cognitive-core.md 마지막의 "적용 가이드"를 따라 커스터마이즈하세요.
