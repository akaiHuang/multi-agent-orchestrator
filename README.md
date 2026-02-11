# Multi-Agent Orchestrator

### GitHub Copilot SDK Agent Coordination

> A framework for orchestrating multiple specialized AI agents using the GitHub Copilot SDK -- enabling parallel development, automated testing, and intelligent task decomposition through coordinated agent sessions.

## About

Multi-Agent Orchestrator 是一個多智能代理協作框架，基於 GitHub Copilot SDK 定義角色分工與任務協調機制。適合用於建立可並行工作的 Agent 團隊（規劃、開發、測試、報告），加速大型任務的自動化交付流程。

## About (EN)

Multi-Agent Orchestrator is a coordination framework built on the GitHub Copilot SDK for role-based AI agent collaboration. It enables parallel planning, implementation, testing, and reporting workflows for complex engineering tasks.

## 📋 Quick Summary

> 🤖 **多智能代理協作框架，讓 AI 團隊像真人團隊一樣分工合作！** 本專案基於 GitHub Copilot SDK 建構完整的多代理協調系統，定義了四種專業角色：🎯 Supervisor（監督者）負責任務分解與進度追蹤、💻 Developer（開發者）負責功能實作與程式碼撰寫、🧪 Tester（測試者）執行自動化測試與錯誤發現、📝 Reporter（報告者）進行結果分析與文件生成。🔄 支援多種工作流程模式——循序執行、平行開發、行銷智慧分析、測試自動化，每種模式都有完整的範例程式碼。🐍 同時提供 TypeScript 與 Python（MarketSense 引擎）雙語言實作。🔥 核心亮點是事件驅動的多 Session 架構，每個代理在獨立 Session 中運行，透過 Firebase Firestore 進行任務佇列管理。📦 內含 16KB 的完整代理定義文件、11KB 的 SDK 使用指南、13KB 的技能配置檔，是學習與部署多代理 AI 系統的絕佳起點。

---

## 🤔 Why This Exists

A single AI agent hits a ceiling quickly on complex software projects. It cannot simultaneously architect, implement, test, and document. It loses context across large codebases. It cannot parallelize.

This project solves that by defining a multi-agent system where each agent is a specialist: a supervisor decomposes tasks and tracks progress, developers implement features in parallel sessions, testers validate code automatically, and reporters synthesize results. All coordinated through the GitHub Copilot SDK's session management and event-driven architecture.

The framework includes ready-to-use agent definitions, skill configurations, orchestration patterns, and a complete guide to building production multi-agent workflows -- in both TypeScript and Python.

---

## 🏗️ Architecture

```
                    Copilot Client
                  (Central Coordinator)
                         |
          +--------------+--------------+
          |              |              |
   Supervisor       Developer(s)     Tester
   Session          Sessions         Session
          |              |              |
   Task Decomposition   Feature        Test
   Progress Tracking    Implementation Execution
   Result Integration   Code Writing   Bug Reports
          |              |              |
          +--------------+--------------+
                         |
                    Reporter Session
                    (Analysis & Documentation)
```

### Agent Roles

| Agent | Role | Tools | Responsibilities |
|-------|------|-------|-----------------|
| **Supervisor** | Project Manager | view, search | Task decomposition, assignment, progress tracking, team coordination |
| **Developer** | Full-Stack Engineer | edit, view, bash, search | Feature implementation, code quality, technical documentation, refactoring |
| **Tester** | QA Engineer | edit, view, bash, search | Unit tests, integration tests, E2E tests, bug discovery, coverage |
| **Reporter** | Technical Writer | view, search | Result analysis, report generation, documentation |

### Orchestration Patterns

The framework supports multiple workflow patterns:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Sequential** | Supervisor -> Developer -> Tester -> Reporter | Standard feature development |
| **Parallel Development** | Multiple developer sessions running simultaneously | Large feature with independent components |
| **Marketing Intelligence** | Specialized agents for market research and strategy | Automated competitive analysis |
| **Test Automation** | Next.js-specific test generation and execution | Frontend testing workflows |

---

## 📂 Key Files

| File | Size | Purpose |
|------|------|---------|
| `agents.md` | 16 KB | Complete agent definitions, architecture diagrams, workflow specifications, and best practices |
| `copilot-sdk-guide.md` | 11 KB | Comprehensive GitHub Copilot SDK usage guide covering client setup, session management, custom agents, MCP servers, and tools |
| `skills.json` | 13 KB | Machine-readable skill definitions with agent roles, capabilities, workflow steps, and prompts |
| `src/` | -- | TypeScript source: Firebase client integration, workflow examples |
| `python/marketsense/` | -- | Python implementation: MarketSense engine for marketing intelligence orchestration |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **SDK** | GitHub Copilot SDK (`@github/copilot-sdk`) |
| **TypeScript** | Node.js 18+, tsx, TypeScript 5.3+ |
| **Python** | MarketSense engine (crawler, analyzer, quality review) |
| **Build** | ESLint, Prettier, tsc |
| **Architecture** | Event-driven, multi-session, parallel execution |
| **Storage** | Firebase Firestore (task queue, analysis results) |

---

## 🏁 Quick Start

### TypeScript (Primary)

```bash
# Install dependencies
npm install

# Run multi-agent workflow (Supervisor + Developer + Tester)
npm run start

# Run parallel development (multiple developer sessions)
npm run parallel

# Run automated testing workflow
npm run test:auto

# Run marketing intelligence orchestration
npm run marketing:intel -- --brief "Brand: X, Product: Y, Target: Z"
```

### Python (MarketSense)

```bash
# Install Python dependencies
cd python && pip install -r requirements.txt

# Run the marketing intelligence pipeline
python -m marketsense.run_pipeline
```

---

## 💡 Session Management Example

```typescript
// Each agent runs in an isolated session
const supervisorSession = await client.createSession({
    sessionId: "supervisor-session",
    customAgents: [supervisorAgent]
});

const devSession = await client.createSession({
    sessionId: "dev-session-1",
    customAgents: [developerAgent]
});

// Parallel execution across sessions
await Promise.all([
    supervisorSession.send({ message: "Decompose the task..." }),
    devSession.send({ message: "Implement the feature..." })
]);
```

---

## 👤 Author

**Huang Akai (Kai)** -- Founder @ Universal FAW Labs | Creative Technologist | Ex-Ogilvy | 15+ years experience

---

## 📄 License

MIT
