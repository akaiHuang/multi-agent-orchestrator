# GitHub Copilot SDK 完整使用指南

## 目錄
- [簡介](#簡介)
- [核心概念](#核心概念)
- [安裝與設置](#安裝與設置)
- [基礎使用](#基礎使用)
- [多代理架構](#多代理架構)
- [進階功能](#進階功能)
- [最佳實踐](#最佳實踐)

## 簡介

GitHub Copilot SDK 是一個強大的開發工具,讓你能夠以程式化方式控制 GitHub Copilot CLI。它提供了一個經過生產驗證的代理執行時環境,你可以透過程式調用它來實現:

- **自動化任務分配**: 將複雜任務分解並分配給多個代理
- **並行開發**: 同時運行多個開發會話,如同擁有多位超級工程師
- **自動監工**: 自動協調和監督多個開發任務
- **自動化測試**: 整合測試流程,確保代碼質量

### 支援的程式語言
- TypeScript/Node.js
- Python
- Go
- .NET/C#

## 核心概念

### 1. CopilotClient (客戶端)
客戶端管理與 Copilot CLI 伺服器的連接,負責:
- 啟動和停止 CLI 伺服器
- 創建和管理會話
- 處理連接狀態

### 2. CopilotSession (會話)
每個會話代表一個獨立的對話,可以:
- 發送訊息和接收回應
- 使用自定義工具
- 串流處理回應
- 維護對話歷史

### 3. Custom Agents (自定義代理)
自定義代理讓你能夠創建專門化的 AI 助手,每個代理可以有:
- 獨特的系統提示詞
- 專屬的工具集
- 特定的 MCP 伺服器
- 自定義能力

### 4. MCP Servers (模型上下文協議伺服器)
MCP 讓代理能夠存取外部工具和數據源。

### 5. Tools (工具)
工具讓代理能夠執行特定操作,如:
- 檔案系統操作
- API 呼叫
- 資料庫查詢
- 自定義業務邏輯

## 安裝與設置

### TypeScript/Node.js
```bash
npm install @github/copilot-sdk
```

### Python
```bash
pip install copilot-sdk
# 或
uv pip install copilot-sdk
```

### Go
```bash
go get github.com/github/copilot-sdk/go
```

### .NET
```bash
dotnet add package GitHub.Copilot.SDK
```

### 前置需求
確保已安裝 GitHub Copilot CLI:
```bash
# 檢查是否安裝
copilot --version

# 如果未安裝,請參考官方文檔
# https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli
```

## 基礎使用

### TypeScript 範例
```typescript
import { CopilotClient } from "@github/copilot-sdk";

// 創建並啟動客戶端
const client = new CopilotClient();
await client.start();

// 創建會話
const session = await client.createSession({
    model: "gpt-4.1",
});

// 使用 Promise 處理回應
const done = new Promise<void>((resolve) => {
    session.on((event) => {
        if (event.type === "assistant.message") {
            console.log("助手:", event.data.content);
        } else if (event.type === "session.idle") {
            resolve();
        }
    });
});

// 發送訊息
await session.send({ prompt: "你好,請幫我解釋什麼是閉包?" });
await done;

// 清理資源
await session.destroy();
await client.stop();
```

### Python 範例
```python
import asyncio
from copilot import CopilotClient

async def main():
    # 創建並啟動客戶端
    client = CopilotClient()
    await client.start()
    
    # 創建會話
    session = await client.create_session({"model": "gpt-4.1"})
    
    # 使用事件處理
    done = asyncio.Event()
    
    def on_event(event):
        if event.type.value == "assistant.message":
            print(f"助手: {event.data.content}")
        elif event.type.value == "session.idle":
            done.set()
    
    session.on(on_event)
    
    # 發送訊息
    await session.send({"prompt": "你好,請幫我解釋什麼是裝飾器?"})
    await done.wait()
    
    # 清理資源
    await session.destroy()
    await client.stop()

asyncio.run(main())
```

## 多代理架構

### 核心理念
多代理架構讓你能夠創建一個由多個專門化代理組成的團隊,每個代理負責特定任務:

1. **開發者代理** - 負責實際編碼
2. **監工代理** - 協調任務和監督進度
3. **測試代理** - 執行自動化測試
4. **審查代理** - 進行代碼審查

### 創建自定義代理

```typescript
import { CopilotClient, CustomAgentConfig } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

// 定義開發者代理
const developerAgent: CustomAgentConfig = {
    name: "developer",
    displayName: "開發工程師",
    description: "專注於編寫高質量代碼的工程師",
    prompt: `你是一位資深全端工程師,專精於:
- 編寫乾淨、可維護的代碼
- 遵循最佳實踐和設計模式
- 實現功能需求
- 撰寫技術文檔`,
    tools: ["edit", "view", "bash"],
    infer: true
};

// 定義監工代理
const supervisorAgent: CustomAgentConfig = {
    name: "supervisor",
    displayName: "專案監工",
    description: "負責任務分配和進度追蹤的專案經理",
    prompt: `你是一位專案經理,負責:
- 將大型任務分解為小任務
- 分配任務給適當的開發者
- 追蹤開發進度
- 協調團隊成員
- 確保專案按時完成`,
    tools: ["view", "search", "bash"],
    infer: true
};

// 定義測試代理
const testerAgent: CustomAgentConfig = {
    name: "tester",
    displayName: "測試工程師",
    description: "專注於自動化測試和質量保證",
    prompt: `你是一位測試工程師,專精於:
- 編寫單元測試和整合測試
- 執行 E2E 測試
- 發現和報告 bug
- 確保代碼覆蓋率
- 使用 Jest、Vitest、Playwright 等測試框架`,
    tools: ["edit", "view", "bash"],
    infer: true
};

// 創建包含所有代理的會話
const session = await client.createSession({
    customAgents: [developerAgent, supervisorAgent, testerAgent],
    model: "gpt-4.1"
});
```

### 並行會話管理

實現真正的多線程開發:

```typescript
async function parallelDevelopment() {
    const client = new CopilotClient();
    await client.start();
    
    // 創建多個獨立會話,每個代表一個開發者
    const devSession1 = await client.createSession({
        sessionId: "dev-worker-1",
        customAgents: [{
            name: "frontend-dev",
            displayName: "前端開發者",
            prompt: "你專精於 React 和 Next.js 開發",
            tools: ["edit", "view", "bash"]
        }]
    });
    
    const devSession2 = await client.createSession({
        sessionId: "dev-worker-2",
        customAgents: [{
            name: "backend-dev",
            displayName: "後端開發者",
            prompt: "你專精於 Node.js API 和資料庫設計",
            tools: ["edit", "view", "bash"]
        }]
    });
    
    const testSession = await client.createSession({
        sessionId: "test-worker",
        customAgents: [{
            name: "qa-engineer",
            displayName: "QA 工程師",
            prompt: "你專精於自動化測試",
            tools: ["edit", "view", "bash"]
        }]
    });
    
    // 並行執行任務
    await Promise.all([
        devSession1.send({ 
            prompt: "創建一個用戶登入表單組件" 
        }),
        devSession2.send({ 
            prompt: "實現用戶認證 API 端點" 
        }),
        testSession.send({ 
            prompt: "為登入流程編寫 E2E 測試" 
        })
    ]);
    
    // ... 監聽各會話的完成事件
}
```

## 進階功能

### 1. 自定義工具

讓代理能夠調用你的自定義功能:

```typescript
import { defineTool } from "@github/copilot-sdk";
import { z } from "zod";

// 定義工具
const deployTool = defineTool({
    name: "deploy_app",
    description: "部署應用程式到指定環境",
    parameters: z.object({
        environment: z.enum(["dev", "staging", "production"]),
        version: z.string()
    }),
    handler: async ({ environment, version }) => {
        // 實現部署邏輯
        console.log(`部署版本 ${version} 到 ${environment}`);
        return {
            success: true,
            message: `成功部署到 ${environment}`
        };
    }
});

// 在會話中使用工具
const session = await client.createSession({
    tools: [deployTool]
});
```

### 2. MCP 伺服器整合

連接外部服務和資料源:

```typescript
const session = await client.createSession({
    mcpServers: {
        "database": {
            type: "local",
            command: "mcp-database-server",
            args: ["--connection-string", process.env.DB_URL],
            tools: ["*"]
        },
        "api-gateway": {
            type: "remote",
            url: "https://api.example.com/mcp",
            headers: {
                "Authorization": `Bearer ${process.env.API_TOKEN}`
            }
        }
    }
});
```

### 3. 串流回應

即時接收助手回應:

```typescript
const session = await client.createSession({
    streaming: true
});

session.on((event) => {
    if (event.type === "assistant.message_delta") {
        // 即時顯示串流內容
        process.stdout.write(event.data.deltaContent || "");
    } else if (event.type === "assistant.message") {
        // 完整訊息
        console.log("\n\n完整回應:", event.data.content);
    }
});
```

### 4. 檔案附件

讓代理處理檔案:

```typescript
await session.send({
    prompt: "請分析這張圖片中的 UI 設計",
    attachments: [{
        type: "file",
        path: "/path/to/design-mockup.png"
    }]
});
```

## 最佳實踐

### 1. 資源管理
```typescript
// 使用 try-finally 確保資源清理
const client = new CopilotClient();
try {
    await client.start();
    const session = await client.createSession();
    
    // 使用會話...
    
    await session.destroy();
} finally {
    await client.stop();
}
```

### 2. 錯誤處理
```typescript
session.on((event) => {
    if (event.type === "error") {
        console.error("錯誤:", event.data);
        // 處理錯誤...
    }
});
```

### 3. 會話恢復
```typescript
// 保存會話 ID
const sessionId = session.sessionId;

// 稍後恢復會話
const resumedSession = await client.resumeSession(sessionId, {
    // 可以添加新的工具或代理
    customAgents: [newAgent]
});
```

### 4. 權限處理
```typescript
const session = await client.createSession({
    onPermissionRequest: async (request) => {
        // 審查權限請求
        console.log("權限請求:", request);
        
        // 批准或拒絕
        return {
            approved: true,
            reason: "已授權執行此操作"
        };
    }
});
```

### 5. 模型選擇
```typescript
// 根據任務選擇合適的模型
const session = await client.createSession({
    model: "gpt-4.1",      // 複雜任務
    // model: "gpt-3.5",   // 簡單任務
    // model: "claude-sonnet-4.5" // 長文本處理
});
```

## 常見問題

### Q: 需要 GitHub Copilot 訂閱嗎?
A: 是的,需要有效的 GitHub Copilot 訂閱。

### Q: 如何計費?
A: SDK 使用與 Copilot CLI 相同的計費方式。

### Q: 支援哪些模型?
A: 所有 Copilot CLI 支援的模型都可用,可通過 `client.listModels()` 查看。

### Q: 可以在生產環境使用嗎?
A: SDK 目前處於技術預覽階段,建議先在開發和測試環境使用。

### Q: 如何回報問題?
A: 請到 [GitHub Issues](https://github.com/github/copilot-sdk/issues) 頁面回報。

## 相關資源

- [官方文檔](https://github.com/github/copilot-sdk)
- [Getting Started Guide](https://github.com/github/copilot-sdk/tree/main/docs/getting-started.md)
- [Cookbook 範例](https://github.com/github/copilot-sdk/tree/main/cookbook)
- [Awesome Copilot](https://github.com/github/awesome-copilot)

---

**版本**: 1.0.0  
**最後更新**: 2026-01-24
