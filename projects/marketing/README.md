# _template — 사업부 복제용 골격

> 이 폴더는 **복제해서 쓰는 템플릿**입니다. 직접 수정하지 마세요.
> 수정하면 나중에 새 사업부 만들 때 오염됩니다.

---

## 쓰는 법

```bash
# 1. 복제
cp -r projects/_template projects/marketing

# 2. Claude 에게 슬롯 채우기 부탁
#    "projects/marketing 의 {{슬롯}} 을 내 사업(네일샵 예약)에 맞춰 채워줘.
#     담당 임원은 CCO + CMO, 스킬은 reels-script 하나만 만들어줘."
```

---

## 구조 (하네스 5종)

```
_template/
├── CLAUDE.md                  ← ① 사업부 헌법
├── agents/
│   └── README.md              ← ② 담당 임원 선언 + @참조
├── skills/
│   └── example-skill.md       ← ③ 업무 매뉴얼 예시
├── context/
│   └── channel-rules.md       ← ④ 채널/환경 규칙
└── rules/
    └── 금지행동.md            ← ⑤ 자동 적용 사규
```

각 파일의 `{{슬롯}}` 만 채우면 첫 사업부 완성입니다. (30~40분)

---

## 다음 단계

- 상위 `projects/README.md` — 왜 쪼개나 + 3대 원칙
- `guides/07_프로젝트_쪼개기.md` — 상세 Step-by-Step 가이드
