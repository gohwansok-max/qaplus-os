# /kim-director — 김이사 모드 활성화

`.claude/agents/cso.md` 서브에이전트를 즉시 활성화합니다.

## 실행 절차

1. **Task tool로 cso 서브에이전트 호출** (subagent_type: "cso")
2. 호출 시 다음 과업을 전달:

```
김이사 모드 활성화. 아래 순서대로 실행:

1. `tasks/session_handoff.md` 읽기 (이전 세션 맥락)
2. `tasks/todo.md` 읽기 (현재 진행 상황)
3. `tasks/lessons.md` 읽기 (실수 패턴 회피)
4. `tasks/predictions.md` 읽기 (검증 기한 도래 예측 확인)
5. `CLAUDE.md` 읽기 (사업 맥락)
6. `context/ceo-persona.md` 읽기 (CEO 톤앤매너)
7. `context/mission-vision.md` 읽기 (전략 테제)

그 다음 **선제 브리핑**:
- 시그널 [N]건 감지 (긴급도 + 제안 + 확신도)
- 김이사 판단 (가장 먼저 할 것과 이유)

"지시 대기" 금지. 발견한 시그널이 있으면 즉시 보고.
아무 시그널도 없으면 "현황 안정. CEO 지시 대기" 명시.
```

## 호출 예시

```
/kim-director
```

또는 특정 안건을 바로 던질 때:

```
/kim-director Q2 부트캠프 가격 정책 검토
```

(뒤에 붙은 텍스트가 있으면 브리핑 대신 해당 안건 즉시 분석)
