# ai-ceo-os

### 9 C-Suite AIs that help a solo CEO run a real business

**Real, working Claude Code subagents** — not a demo, not a prompt pack. The actual 9-agent system used internally at AINOW (에이나우), open-sourced.

- **CSO "Kim"** (Chief of Staff / Strategy) + **CMO / CFO / CTO / CDO / COO / CCO / CPO / CXO**
- Each executive is a real `.claude/agents/*.md` subagent — invoked by Claude Code's Task tool, not roleplay
- **3-Tier operation**: Kim alone (90%), 2–3 execs in parallel (9%), all 8 + rebuttal round (1%)
- First-principles thinking + Staff ×C-Suite matrix + confidence scoring + Zero-Inference Rule
- Every decision includes Cross-Lens self-check + Inversion (3 ways this proposal fails)

> The internal AINOW system runs 68+ agents across the full stack. **This repo open-sources the core 9 C-Suite layer.** It's a skeleton — you must fill in your own business data, strategy, and content formulas.

---

## What's inside

### 1. 9 C-Suite Subagents (real, not simulated)
`.claude/agents/{cso,cmo,cfo,cto,cdo,coo,cco,cpo,cxo}.md`

Each contains:
- YAML frontmatter (`name`, `description`, `tools`)
- Full **Cognitive Core** inline (first-principles, 4 thinking tools, MUST Disagree conditions, confidence scoring, Cross-Lens, Inversion)
- Domain-specific persona, questions, lenses, internal staff of 4, reporting template

### 2. `/kim-director` slash command
`.claude/commands/kim-director.md` — Auto-invokes the CSO subagent with the preemptive briefing protocol: scan handoff/todo/lessons/predictions → detect signals → propose next actions with confidence scores.

### 3. 5 Fully-Public Skills (with self-grading rubrics)
- `skills/content/reels-script/` — Reels script × 3 versions + captions × 3 (12 hook types)
- `skills/strategy/weekly-briefing/` — Weekly briefing with risk-first layout + system hygiene check
- `skills/strategy/monthly-business-review/` — Monthly OKR / P&L / AI ops cost review
- `skills/marketing/sales-analysis/` — C.L.O.S.E funnel diagnosis
- `skills/edutech/course-design/` — L.E.A.R.N curriculum design

### 4. 3 Gold-Standard Workflows
With actual `Task(subagent_type=...)` invocation blocks, not just flowcharts:
- `workflows/examples/weekly-briefing.md`
- `workflows/examples/content-calendar.md`
- `workflows/examples/reels-script-pipeline.md`

### 5. Example Scripts
- `execution/sales_summary_sample.py` — Daily/monthly sales aggregation (167 lines, runnable)
- `execution/instagram_stats_fetch.py` — Instagram Graph API template
- `scripts/git_backup.sh` — Daily auto-backup with cron setup guide

### 6. Complete Example: Solo Freelance Designer
`examples/1인-프리랜서-디자이너/` — A fictional persona "Park Soyoung" with 100% filled-in `CLAUDE.md`, personas, channel rules, mission, tasks (with real lessons and predictions from "1 month of operation"), and a custom domain-specific skill.

This is what "the template filled out" actually looks like.

---

## Quick Start

```bash
# 1. Install Claude Code (one-time)
npm install -g @anthropic-ai/claude-code

# 2. Extract the ZIP you received (or git clone once public)
cd ai-ceo-os

# 3. Launch
claude

# 4. Run setup (AI interviews you about your business)
/setup

# 5. Check everything is working
./scripts/doctor.sh
```

> **First time?** → See [`INSTALL.md`](INSTALL.md) for a 3-minute setup guide.

---

## Project Structure

```
ai-ceo-os/
├── .claude/
│   ├── agents/          ← 9 C-Suite subagents (real)
│   ├── commands/        ← /setup, /kim-director
│   ├── rules/           ← Cross-cutting rules
│   └── settings.json    ← Permissions + statusLine
│
├── agents/              ← Persona documentation (human-readable)
├── context/             ← CEO persona, mission/vision, channel rules
├── knowledge/           ← Your data repository (channel stats, strategy refs)
├── skills/              ← Reusable work manuals (5 fully public)
├── workflows/           ← Pipelines (3 gold-standard examples)
├── execution/           ← Python scripts (Zero-Inference data sources)
├── scripts/             ← Infrastructure (backup, alerts, cron)
├── examples/            ← Complete filled-in samples by industry
├── tasks/               ← todo, lessons, predictions, session_handoff
└── guides/              ← Onboarding, customization, tools
```

---

## Core Operating Principles

### 1. Zero-Inference Rule
AI never computes numbers directly. All metrics come from scripts in `execution/` or cited data sources. If no data exists, the answer is **"data required"** — not a guess.

### 2. Confidence Scoring (Mandatory)
Every strategic proposal must carry a confidence percentage:
- **"Confident" (80%+)** — data + experience + logic align
- **"Hypothesis" (50–79%)** — logic present but data insufficient → test recommended
- **"Gut" (<50%)** — explicitly flagged, verification method proposed

### 3. MUST Disagree Protocol
All agents must disagree (not acquiesce) when a proposal contradicts data, the strategic thesis, ROI logic, or repeats a documented failure pattern.

### 4. Cross-Lens + Inversion (Required in every report)
Every report ends with:
- Cross-Lens: how does this affect 2 other domains?
- Inversion: 3 scenarios that would ruin this proposal, with early warning signals

### 5. Self-Annealing
Every mistake goes into `tasks/lessons.md` with 5 Whys root-cause analysis. Every strategic judgment goes into `tasks/predictions.md` with a verification date. Agent judgment quality becomes measurable over 6 months.

---

## Why this exists

Most "AI agent" repos are prompt collections — they demo well but fail in production because they lack:
1. Independent subagent execution (not 1 Claude pretending to be 9)
2. Structured decision protocols (3-Tier, routing, rebuttal rounds)
3. A learning loop (lessons + predictions + session handoff)
4. Cross-domain self-check (Cross-Lens)
5. Adversarial self-review (Inversion)

ai-ceo-os encodes all 5 into a workable skeleton. Fill in your business data and you have a working AI executive team.

---

## License

MIT License. See `LICENSE` for details.

Contributions welcome — see `CONTRIBUTING.md`.
Security issues — see `SECURITY.md`.
Code of conduct — see `CODE_OF_CONDUCT.md`.

---

## Want to build this for your own business?

This repo is the skeleton.
The bootcamp is where you learn to fill in the flesh — live, with the CEO walking you through it on real business data.

→ **60-day AI Producer Monetization Bootcamp** (link announced on AINOW official channels)

---

## Star History

If this repo helps you, please star it. Stars help discover the project.

---

🇰🇷 한국어 README → [`README.md`](README.md)
