# CTO Lessons — 기술+인프라 실수 누적

> cognitive-core.md § 6.1로 보고 시작 전 자동 로드.

---

## 시작 — 본인 사업의 기술 교훈을 여기에 누적하세요

### 시드 원칙
- **롤백 1분 내 불가능한 배포 금지**
- **단일 장애점(SPOF) 신규 생성 금지**: Auto Recovery/Failover 필수
- **API 키/토큰 만료 사전 알림**: 만료 7일 전 자동 경고
- **Build vs Buy vs Borrow**: 직접 만들기 전 SaaS/오픈소스 먼저 검토
- **테스트 없이 프로덕션 배포 금지**
