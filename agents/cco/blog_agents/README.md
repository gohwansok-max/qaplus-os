# 큐에이플러스(QA+) 4인 블로그 에이전트 팀 (Blog Agent Team)

> Claude Code / Claude CoWork / Antigravity / n8n 환경에서 20년 식품품질 전문가의 지식을 고품질 블로그 원고로 자동 변환하는 4단계 에이전트 파이프라인입니다.

---

## 👥 에이전트 팀 구성 및 역할

```
[사용자 입력: 주제 한 줄]
         ↓
  1. 01_research_agent.md (키워드 분석, 검색 의도, 법령/기준서 출처, 목차 설계)
         ↓
  2. 02_writer_agent.md (20년 멘토 선배 톤앤매너, Zero Filler, 실무 꿀팁 원고 작성)
         ↓
  3. 03_image_agent.md (썸네일, 본문 인포그래픽 프롬프트, Mermaid 차트 기획)
         ↓
  4. 04_editor_agent.md (사실관계/법령 검수, SEO 메타데이터, Markdown & HTML 패키징)
         ↓
[최종 결과물: 네이버 블로그/티스토리/워드프레스 즉시 발행용 파일]
```

---

## 📁 파일 구성
- `01_research_agent.md` — 리서치 및 기획 에이전트
- `02_writer_agent.md` — 수석 작가 에이전트
- `03_image_agent.md` — 시각자료 & 인포그래픽 디자이너 에이전트
- `04_editor_agent.md` — 편집장 & QA 검수 에이전트

---

## 🚀 실행 방법 2가지
1. **안티그래비티 자체 실행기 (추천/가장 간편)**:
   - 채팅창에 `블로그 작성해줘: {원하는 주제}` 입력 또는 `python scripts/generate_blog.py --topic "{주제}"` 실행
   - 4개 에이전트가 순차 협업하여 `outputs/blog/` 폴더에 즉시 파일 생성
2. **n8n 워크플로우 실행기**:
   - `workflows/blog-automation/start_n8n.bat` 실행 후 n8n에서 `n8n_blog_agent_pipeline.json` 불러오기
