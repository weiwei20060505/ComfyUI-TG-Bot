# Telegram + ComfyUI AI 繪圖機器人需求文檔

## 1. 專案目標

本專案使用 Python 開發一個 Telegram 機器人，連接本地端 ComfyUI 進行 AI 文生圖。

使用者只需在 Telegram 輸入自然語言，系統會：

1. 接收使用者文字訊息。
2. 調用 Gemini API，將自然語言轉換為結構化繪圖需求。
3. 由 Gemini 根據可用工作流資訊，自動選擇最適合的 ComfyUI workflow。
4. 將 Gemini 輸出的參數寫入對應 workflow 的指定節點。
5. 將任務送至本地 ComfyUI。
6. 等待生成完成。
7. 只將最終圖片檔回傳給 Telegram 使用者。
8. 在後台保存請求、錯誤與最新生成圖片。

本需求文檔偏向工程實作規格。

## 2. 範圍

### 2.1 本階段支援

- 僅支援文字生圖。
- 每次使用者請求只生成一張圖片。
- Telegram 回覆內容只包含圖片檔本身。
- 生成參數、workflow 選擇、錯誤與執行紀錄只寫入後台日誌。
- 多使用者請求需排隊處理。
- 生成過程需提供狀態訊息。
- ComfyUI 預設連線位址為 `http://127.0.0.1:8188`。
- 敏感設定必須放在 `.env`。
- 架構需保留未來 Docker 化彈性。

### 2.2 本階段不支援

- 不支援圖生圖。
- 不支援參考圖。
- 不支援局部重繪。
- 不支援一次生成多張圖片。
- 不需要 Telegram 指令，例如 `/start`、`/help`、`/cancel`。
- 不限制 Telegram 使用者，但需保留未來加入白名單或權限控管的空間。
- 不允許使用者明確指定 workflow，workflow 選擇完全交給 Gemini 判斷。

## 3. 使用者流程

1. 使用者在 Telegram 傳送自然語言，例如「畫一位雨夜街頭的 cyberpunk 女孩，電影感，霓虹燈」。
2. Bot 回覆狀態訊息，例如「已收到需求，正在理解畫面」。
3. Bot 將使用者輸入、可用 workflow 描述、可用參數規格送給 Gemini。
4. Gemini 回傳結構化結果。
5. Bot 回覆狀態訊息，例如「正在排隊生成」或「正在生成圖片」。
6. Bot 根據 Gemini 結果載入指定 workflow。
7. Bot 替換 workflow 中設定檔指定的節點欄位。
8. Bot 送出任務至 ComfyUI。
9. Bot 在 timeout 內輪詢或等待生成結果。
10. 成功時，Bot 將圖片傳回 Telegram。
11. 失敗時，Bot 顯示友善錯誤訊息。

## 4. 系統架構

建議拆分為以下模組：

- `bot`
  - 負責 Telegram 訊息接收、狀態回覆、圖片回傳。
- `queue`
  - 負責請求排隊，確保 ComfyUI 任務逐一執行。
- `gemini_parser`
  - 負責調用 Gemini API，將自然語言轉成結構化參數。
- `workflow_registry`
  - 負責動態讀取 `workflow` 資料夾內的 workflow 與設定檔。
- `workflow_renderer`
  - 負責將 Gemini 參數寫入 ComfyUI workflow graph。
- `comfyui_client`
  - 負責呼叫 ComfyUI API、查詢任務狀態、取得生成圖片。
- `storage`
  - 負責保存日誌與最新生成圖片。
- `config`
  - 負責讀取 `.env` 與應用程式設定。

## 5. 目錄結構建議

```text
comfyui_tg_bot/
  main.py
  proposal.md
  .env
  .env.example
  workflow/
    test.json
    test.config.json
  logs/
    requests.log
    errors.log
  output/
    latest/
      latest.png
```

其中：

- `workflow/*.json`：ComfyUI prompt graph。
- `workflow/*.config.json`：對應 workflow 的描述與節點映射設定。
- `logs/`：保存純文字日誌。
- `output/latest/`：保存最新生成圖片。

`logs/` 與 `output/` 是否進入 git 需由後續實作決定，但敏感資料與生成結果預設不應提交。

## 6. Workflow 設計

### 6.1 動態擴充要求

workflow 不應寫死在程式碼中。

系統啟動時需掃描 `workflow` 資料夾，讀取所有可用 workflow 及其設定檔。未來新增 workflow 時，應只需要新增 workflow graph 與對應設定檔，不需要修改核心程式邏輯。

### 6.2 Workflow graph

ComfyUI workflow graph 以 JSON 形式放置於 `workflow` 資料夾。

目前測試檔案為：

```text
workflow/test.json
```

此檔案包含 ComfyUI 節點 graph。依目前測試檔結構，可觀察到以下節點：

- `3`：`KSampler`
- `5`：`EmptyLatentImage`
- `6`：正向提示詞 `CLIPTextEncode`
- `7`：反向提示詞 `CLIPTextEncode`
- `9`：`SaveImage`

實作時不得假設所有 workflow 都使用相同節點 id。節點 id 必須由 workflow 設定檔提供。

### 6.3 Workflow 設定檔

每個 workflow 應搭配一個設定檔，用來描述：

- workflow id
- workflow 名稱
- workflow 描述
- 適用場景
- Gemini 選擇 workflow 時可讀取的摘要
- 需要 Gemini 輸出的欄位
- 欄位對應到 ComfyUI graph 的節點與 input key
- 支援的長寬比與固定尺寸對照
- 預設參數

設定檔建議使用 JSON，檔名與 workflow graph 對應：

```text
workflow/test.json
workflow/test.config.json
```

建議格式如下：

```json
{
  "id": "test",
  "name": "Test Anime Workflow",
  "description": "測試用動漫風文生圖工作流",
  "selection_hint": "適合動漫、二次元、角色插畫、日系風格",
  "workflow_file": "test.json",
  "fields": {
    "positive_prompt": {
      "required": true,
      "target": {
        "node_id": "6",
        "input": "text"
      }
    },
    "negative_prompt": {
      "required": true,
      "target": {
        "node_id": "7",
        "input": "text"
      }
    },
    "width": {
      "required": true,
      "target": {
        "node_id": "5",
        "input": "width"
      }
    },
    "height": {
      "required": true,
      "target": {
        "node_id": "5",
        "input": "height"
      }
    },
    "seed": {
      "required": false,
      "target": {
        "node_id": "3",
        "input": "seed"
      }
    }
  },
  "aspect_ratios": {
    "1:1": {
      "width": 1024,
      "height": 1024
    },
    "16:9": {
      "width": 1344,
      "height": 768
    },
    "9:16": {
      "width": 768,
      "height": 1344
    }
  },
  "defaults": {
    "negative_prompt": "text, watermark",
    "aspect_ratio": "1:1"
  }
}
```

實際欄位可依不同 workflow 增減。Gemini 需要輸出的結構應以各 workflow 設定檔為準。

## 7. Gemini 解析需求

### 7.1 輸入

Gemini prompt 需包含：

- 使用者原始自然語言。
- 所有可用 workflow 的 `id`、`name`、`description`、`selection_hint`。
- 各 workflow 需要的欄位規格。
- 支援的長寬比選項。
- 回傳 JSON schema 要求。

### 7.2 輸出

Gemini 必須回傳可被程式解析的 JSON，不應回傳自然語言段落。

建議輸出格式：

```json
{
  "workflow_id": "test",
  "positive_prompt": "masterpiece, best quality, ...",
  "negative_prompt": "text, watermark, low quality, ...",
  "aspect_ratio": "1:1",
  "parameters": {
    "seed": null
  }
}
```

`parameters` 內容應根據所選 workflow 設定檔動態決定。

### 7.3 模糊輸入

當使用者輸入模糊時，不追問使用者。

Gemini 應自動補全畫面主體、風格、構圖、光線、細節與反向提示詞。

### 7.4 Workflow 選擇

workflow 選擇完全交給 Gemini。

即使使用者文字中包含風格描述，Bot 也不直接解析或覆蓋 workflow 選擇，而是把使用者輸入交給 Gemini，由 Gemini 根據可用 workflow 設定判斷。

### 7.5 Gemini 失敗處理

Gemini API 調用失敗時：

1. 自動重試 1 次。
2. 若仍失敗，改用預設解析與參數。
3. 將錯誤寫入後台錯誤日誌。
4. 不向 Telegram 使用者顯示 Gemini 或程式碼錯誤。

預設解析需從可用 workflow 中選擇一個明確標記為 default 的 workflow。若沒有 default workflow，系統啟動時應報錯並要求補齊設定。

## 8. 長寬比與尺寸

使用者可以自然語言描述橫圖、直圖、正方形等需求。

Gemini 需將其轉換為 workflow 設定檔中支援的 `aspect_ratio`。

Bot 不直接讓任意比例進入 ComfyUI，而是根據設定檔將長寬比轉成固定尺寸。

例如：

```json
{
  "1:1": {
    "width": 1024,
    "height": 1024
  },
  "16:9": {
    "width": 1344,
    "height": 768
  },
  "9:16": {
    "width": 768,
    "height": 1344
  }
}
```

實際尺寸以各 workflow 設定檔為準。

## 9. ComfyUI 串接需求

### 9.1 連線設定

ComfyUI 預設 API base URL：

```text
http://127.0.0.1:8188
```

此值需可透過 `.env` 覆蓋。

### 9.2 任務提交

Bot 應使用 ComfyUI API 提交 prompt graph。

提交前需完成：

- 載入所選 workflow graph。
- 依 workflow 設定檔替換正向提示詞。
- 依 workflow 設定檔替換反向提示詞。
- 依長寬比替換 width 與 height。
- 依設定檔替換其他必要參數。
- 確保 batch size 為 1，除非 workflow 設定檔另有明確設定。

### 9.3 生成結果取得

Bot 需在任務完成後取得最終圖片。

若 ComfyUI 返回多個圖片結果，本階段只取第一張作為 Telegram 回傳圖片。

### 9.4 Timeout

單次生成任務 timeout 為 3 分鐘。

超過 3 分鐘視為失敗，Bot 應向使用者回覆：

```text
伺服器目前休息中或過載，請稍後再試
```

同時將 timeout 詳情寫入後台錯誤日誌。

## 10. Telegram Bot 行為

### 10.1 訊息處理

Bot 接收一般文字訊息作為繪圖請求。

本階段不需要支援 Telegram 指令。

若使用者傳送非文字訊息，例如圖片、貼圖、語音或檔案，Bot 應友善提示目前只支援文字描述。

### 10.2 狀態訊息

Bot 應在關鍵階段提供狀態回覆。

建議狀態：

- 已收到需求，正在理解畫面。
- 正在排隊生成。
- 正在生成圖片。
- 圖片完成後直接回傳圖片。

具體文案可在實作階段調整，但不得向使用者暴露內部錯誤堆疊、API payload 或程式碼錯誤。

### 10.3 排隊處理

多個使用者同時請求時，任務需排隊處理。

本階段要求同一時間只送出一個 ComfyUI 生成任務，避免本地 ComfyUI 過載。

佇列需記錄：

- Telegram chat id
- Telegram user id
- 使用者原始輸入
- 任務建立時間
- 任務開始時間
- 任務完成或失敗時間
- workflow id
- Gemini 解析結果

### 10.4 使用者限制

本階段不限制使用者。

但架構需保留未來加入以下功能的空間：

- Telegram user id 白名單。
- 每日使用次數限制。
- 每位使用者佇列限制。

## 11. 錯誤處理

### 11.1 Gemini API 失敗

處理規則：

- 自動重試 1 次。
- 第二次仍失敗時使用預設解析與參數。
- 錯誤寫入 `logs/errors.log`。
- 使用者端繼續流程，除非預設解析也不可用。

### 11.2 Gemini 回傳格式錯誤

處理規則：

- 視為 Gemini 解析失敗。
- 可重試 1 次。
- 若仍失敗，使用預設解析與參數。
- 記錄原始回應與驗證錯誤。

### 11.3 Workflow 不存在

若 Gemini 回傳不存在的 `workflow_id`：

- 使用 default workflow。
- 記錄錯誤與 Gemini 原始輸出。

### 11.4 Workflow 設定不完整

若 workflow 設定檔缺少必要欄位：

- 系統啟動時應檢查並報錯。
- 不應等到使用者請求時才失敗。

### 11.5 ComfyUI 未啟動或生成失敗

若 ComfyUI 無法連線、任務提交失敗、任務執行失敗或結果圖片取得失敗，使用者端統一提示：

```text
伺服器目前休息中或過載，請稍後再試
```

後台需記錄詳細錯誤。

### 11.6 生成逾時

若任務超過 3 分鐘：

- 中止等待。
- 回覆友善錯誤訊息。
- 寫入錯誤日誌。

是否要主動向 ComfyUI 發出取消任務請求，需依後續 ComfyUI API 實作能力確認。

## 12. 日誌與檔案保存

### 12.1 請求日誌

保存純文字請求紀錄至：

```text
logs/requests.log
```

每筆紀錄至少包含：

- timestamp
- Telegram chat id
- Telegram user id
- 使用者原始輸入
- workflow id
- Gemini 結構化輸出
- 最終送往 ComfyUI 的主要參數
- 任務結果
- 耗時

### 12.2 錯誤日誌

保存純文字錯誤紀錄至：

```text
logs/errors.log
```

每筆紀錄至少包含：

- timestamp
- error type
- error message
- traceback 或可診斷資訊
- 對應 Telegram user id
- 對應 workflow id
- 對應請求摘要

### 12.3 最新圖片

保存最新生成圖片至：

```text
output/latest/
```

本階段只要求保存最新生成圖片，不要求建立完整歷史圖庫。

若每次覆蓋 `latest.png`，仍需在請求日誌中記錄本次任務成功。

## 13. 設定需求

敏感設定必須放在 `.env`。

建議 `.env` 欄位：

```text
TELEGRAM_BOT_TOKEN=
GEMINI_API_KEY=
COMFYUI_BASE_URL=http://127.0.0.1:8188
WORKFLOW_DIR=workflow
LOG_DIR=logs
OUTPUT_DIR=output
GENERATION_TIMEOUT_SECONDS=180
```

建議提供 `.env.example`，但不得在其中放入真實 token 或 API key。

## 14. 相依套件

目前 `pyproject.toml` 已包含以下主要套件：

- `python-telegram-bot`
- `google-genai`
- `aiohttp`
- `pydantic`
- `python-dotenv`

實作時應優先使用現有依賴。

若需要新增依賴，需確認其用途與必要性。

## 15. 資料驗證

Gemini 回傳結果必須經過資料驗證後才能送入 ComfyUI。

建議使用 Pydantic 定義模型：

- `GeminiParseResult`
- `WorkflowConfig`
- `WorkflowFieldMapping`
- `AspectRatioSize`
- `GenerationJob`

驗證重點：

- `workflow_id` 必須存在。
- `aspect_ratio` 必須存在於該 workflow 設定檔。
- 必填欄位不可為空。
- target node id 必須存在於 workflow graph。
- target input key 必須存在於該節點 inputs。
- width 與 height 必須是正整數。

## 16. 啟動檢查

Bot 啟動時需執行基本檢查：

- `.env` 必要欄位存在。
- `workflow` 資料夾存在。
- 至少存在一組可用 workflow。
- 每個 workflow graph 都有對應設定檔。
- 所有 workflow 設定檔可被解析。
- 所有設定檔指定的節點 id 與 input key 存在。
- 至少一個 workflow 被標記為 default。

ComfyUI 是否必須在啟動時可連線，需在實作階段確認。若不強制啟動檢查，則需在第一筆請求時友善處理連線失敗。

## 17. 非功能需求

### 17.1 可維護性

- workflow 新增與調整不應要求修改核心程式碼。
- Gemini prompt 組裝邏輯應集中管理。
- ComfyUI API 呼叫應封裝在獨立 client。
- Telegram 互動邏輯不應直接操作 workflow JSON。

### 17.2 可觀測性

- 所有失敗需寫入錯誤日誌。
- 所有請求需寫入請求日誌。
- 日誌需足以重現當次主要參數。

### 17.3 安全性

- `.env` 不得提交至版本控制。
- Telegram token 與 Gemini API key 不得寫入日誌。
- 使用者端不顯示內部錯誤。

### 17.4 Docker 化彈性

目前於本機執行，但設計時需避免硬編碼本機絕對路徑。

所有路徑與服務 URL 應透過設定取得。

## 18. 驗收條件

完成實作後，至少需滿足以下條件：

1. 使用者在 Telegram 傳送文字後，Bot 能回覆狀態訊息。
2. Bot 能調用 Gemini 並取得結構化 JSON。
3. Gemini 失敗時，Bot 能重試 1 次並 fallback 至預設參數。
4. Bot 能動態讀取 `workflow` 資料夾中的 workflow 與設定檔。
5. Bot 能依設定檔替換 ComfyUI workflow 的 prompt、negative prompt、width、height。
6. Bot 能將任務送往 `http://127.0.0.1:8188` 或 `.env` 指定的 ComfyUI。
7. Bot 能在任務成功後只回傳圖片給 Telegram 使用者。
8. 多個請求會排隊，不會同時送入 ComfyUI。
9. ComfyUI 未啟動、生成失敗或 timeout 時，使用者只看到友善錯誤訊息。
10. 請求與錯誤會寫入純文字日誌。
11. 最新生成圖片會保存到指定資料夾。
12. 新增 workflow 時，只需新增 workflow graph 與設定檔，不需修改核心程式碼。

## 19. 待確認事項

以下事項目前尚未完全確定，實作前或實作中需再確認：

1. 各 workflow 的實際清單、名稱、用途與選擇提示。
2. 每個 workflow 的最終節點映射設定。
3. 各 workflow 支援的固定尺寸與長寬比列表。
4. default workflow 應是哪一個。
5. 預設解析失敗時要使用的 fallback 正向提示詞與反向提示詞。
6. ComfyUI 任務 timeout 後是否需要主動取消佇列中的任務。
7. 最新生成圖片是否永遠覆蓋同一檔名，或以 timestamp 保存最近一張後再同步為 `latest.png`。
