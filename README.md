# Multi-Agent Orchestrator

### GitHub Copilot SDK Agent Coordination

> A framework for orchestrating multiple specialized AI agents using the GitHub Copilot SDK -- enabling parallel development, automated testing, and intelligent task decomposition through coordinated agent sessions.

---

## Why This Exists

A single AI agent hits a ceiling quickly on complex software projects. It cannot simultaneously architect, implement, test, and document. It loses context across large codebases. It cannot parallelize.

This project solves that by defining a multi-agent system where each agent is a specialist: a supervisor decomposes tasks and tracks progress, developers implement features in parallel sessions, testers validate code automatically, and reporters synthesize results. All coordinated through the GitHub Copilot SDK's session management and event-driven architecture.

The framework includes ready-to-use agent definitions, skill configurations, orchestration patterns, and a complete guide to building production multi-agent workflows -- in both TypeScript and Python.

---

## Architecture

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

## Key Files

| File | Size | Purpose |
|------|------|---------|
| `agents.md` | 16 KB | Complete agent definitions, architecture diagrams, workflow specifications, and best practices |
| `copilot-sdk-guide.md` | 11 KB | Comprehensive GitHub Copilot SDK usage guide covering client setup, session management, custom agents, MCP servers, and tools |
| `skills.json` | 13 KB | Machine-readable skill definitions with agent roles, capabilities, workflow steps, and prompts |
| `src/` | -- | TypeScript source: Firebase client integration, workflow examples |
| `python/marketsense/` | -- | Python implementation: MarketSense engine for marketing intelligence orchestration |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **SDK** | GitHub Copilot SDK (`@github/copilot-sdk`) |
| **TypeScript** | Node.js 18+, tsx, TypeScript 5.3+ |
| **Python** | MarketSense engine (crawler, analyzer, quality review) |
| **Build** | ESLint, Prettier, tsc |
| **Architecture** | Event-driven, multi-session, parallel execution |
| **Storage** | Firebase Firestore (task queue, analysis results) |

---

## Quick Start

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

## Session Management Example

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

## Author

**Huang Akai (Kai)** -- Founder @ Universal FAW Labs | Creative Technologist | Ex-Ogilvy | 15+ years experience

---

## License

MIT
