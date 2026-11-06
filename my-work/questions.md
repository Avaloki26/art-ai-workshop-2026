# 課堂提問與待確認事項

## 2026-11-06｜課前環境與目錄整合測試

> 本次沒有卡住超過 30 分鐘。原本的兩個障礙（fork／推送授權）已經解決；以下是完整紀錄與仍可改進的地方。

### 1. Fork、remote 與推送都已完成

- 本地路徑：`/Users/kayiho/Documents/Default Project`
- 你的 fork（`origin`）：`https://github.com/Avaloki26/art-ai-workshop-2026.git`
- 官方倉庫（`upstream`）：`https://github.com/boan-anbo/art-ai-workshop-2026.git`
- 分支與基底版本：`main`，`2fea758`
- 第一個 commit：`e9f01af`（`Add first source index and reading note for SRC-001`）
- 已推上 fork：`origin/main` 目前指向 `e9f01af`
- 已做：建立 fork、設定 `origin`／`upstream`、`git fetch --all`、commit、`git push -u origin main`。

### 2. Git 提交身分（可隨時更改）

- 姓名：`Avaloki26`
- Email：`352713637+Avaloki26@users.noreply.github.com`
- 只寫在這個倉庫的 `.git/config`，沒有改動全域 Git 設定。
- 若你想改用真實姓名或學校／個人 Email，請告知；可在下一個 commit 前修改。

### 3. 推送授權（已解決）

原始錯誤（保留供日後排查）：

```text
remote: No anonymous write access.
fatal: Authentication failed for 'https://github.com/Avaloki26/art-ai-workshop-2026.git/'
fatal: could not read Username for 'https://github.com': Device not configured
```

解決方式：

1. `brew install gh`（GitHub CLI 2.103.3）。
2. `gh auth login --hostname github.com --git-protocol https --web`，在瀏覽器以 `Avaloki26` 完成裝置授權。
3. `gh auth setup-git`，讓 Git 透過 `gh` 取得 GitHub 憑證。
4. `git push -u origin main` 成功。

### 4. 終端機的 `git` 路徑（已解決）

- 原本現象：直接執行 `git` 會先找到 `/usr/bin/git`，但這台電腦缺少 Xcode Command Line Tools，會跳出安裝提示：

  ```text
  xcode-select: note: No developer tools were found, requesting install.
  ```

- 已做：建立 `~/.zprofile`，加入
  ```sh
  eval "$(/opt/homebrew/bin/brew shellenv)"
  ```
- 驗證：以 `zsh -l` 開啟登入 shell 後，`git` 指向 `/opt/homebrew/bin/git`（2.56.0），`gh` 指向 `/opt/homebrew/bin/gh`（2.103.3）。
- 注意：已經開著的終端機不會自動套用，需重開終端機或執行 `source ~/.zprofile`。

---

## 2026-11-06｜OpenRouter API 整合測試（暫停，待課堂討論）

> **依 30 分鐘規則停下**：金鑰設定從 14:23 進行到 15:13，約 50 分鐘，超過門檻。
> 目前為止**沒有成功完成任何一次模型呼叫，也沒有產生任何費用**（失敗請求不計費）。

### 1. 金鑰與 `.gitignore`（已完成）

- `.env` 存在，權限 `600`，內容含有效的 `OPENROUTER_API_KEY`（73 字元）。
- `.gitignore:7` 忽略 `.env`；`.gitignore:15` 忽略 `my-work/artifacts/*`。
- `git ls-files .env` 查無此檔 → 從未被 Git 追蹤。
- 免費的 `GET https://openrouter.ai/api/v1/key` 查詢結果：金鑰有效、`usage = 0`、`is_free_tier = false`。
- 金鑰全程未列印、未貼進對話、未寫入任何會被 commit 的檔案。

### 2. 障礙 A：剪貼簿內容被回覆文字覆蓋（已繞過）

- 現象：在網站按「複製金鑰」後回報「複製好了」，但 `pbpaste` 連續兩次讀到的都是 `複製好了` 這四個字。
- 推測原因：送出聊天訊息時剪貼簿被覆蓋，或網站的複製按鈕未成功寫入剪貼簿。
- 另一個更早的現象：第一次貼進 `.env` 的值只有 18 字元，結構為 `a00...00a`，是 OpenRouter 列表上的**打碼顯示**（`sk-or-v1-a12...34b`），不是金鑰本體。
- 解法：改用 OpenCode 內建瀏覽器登入 OpenRouter → `New key` → 建立 `art-ai-workshop` → 按 `Copy key to clipboard` → 同一個回合內用 Python 從剪貼簿讀取、以 `^sk-or-v1-[0-9a-f]{64}$` 驗證、寫入 `.env`（不顯示內容）。

### 3. 障礙 B：Gemini 在香港被地區限制（未解決）

執行指令：

```sh
python3 my-work/research/api-test-2026-11-06/run_api_test.py --vision
```

完整錯誤（已存 `my-work/artifacts/api-test-2026-11-06/vision-error.json`）：

```json
{"error":{"message":"This model is not available in your region.","code":403,
"metadata":{"routing_funnel":[{"step":"Initial Endpoints","endpoint_count":8},
{"step":"Filter by Regional Surcharge","endpoint_count":6}],
"failed_routing_step":"Gate Endpoints with Geo Restrictions"}}}
```

- 模型：`google/gemini-3.1-flash-lite`
- 白話：香港不在 Google 模型允許的地區，OpenRouter 在路由階段就攔截，請求未送到模型。
- 費用：**$0**（失敗請求不計費）。

**可替代的視覺模型（價格為官方 models API 查得，每百萬 token）**

| 模型 | 輸入 | 輸出 | 單次預估 |
|---|---|---|---|
| `qwen/qwen3-vl-30b-a3b-instruct` | $0.15 | $0.60 | < $0.001 |
| `qwen/qwen3-vl-8b-instruct` | $0.25 | $0.75 | < $0.001 |
| `z-ai/glm-4.6v` | $0.30 | $0.90 | < $0.001 |

**待你確認後可執行的指令**（把模型換掉，其餘不變）：

```sh
python3 my-work/research/api-test-2026-11-06/run_api_test.py \
  --vision --vision-model qwen/qwen3-vl-30b-a3b-instruct
```

### 4. 障礙 C：Embedding 測試尚未執行

- 你選擇先暫停，因此 `cohere/embed-5-fast` 的圖文相似度測試**尚未呼叫**，無費用。
- 若之後要跑（約 $0.0002–0.0005）：

```sh
python3 my-work/research/api-test-2026-11-06/run_api_test.py --embedding
```

- 風險：Cohere 也可能有地區限制；若出現同樣的 403，需改用其他多模態 embedding 模型（例如 `mongodb/voyage-multimodal-3.5`）。

### 5. 安全性待辦（建議由上課前完成）

- 這次建立的 `art-ai-workshop` 金鑰設定為 **No expiration + No limit**。
- 建議到 https://openrouter.ai/settings/keys 給它設一個 **credit limit（例如 $5）**，降低外洩時的損失。
- 另外兩把舊金鑰（`workshop test 11062`、`art-ai-workshop 1106`）將於 **2026-11-07** 到期，不用時可刪除。

### 6. 本次產生的檔案

| 路徑 | 用途 | Git |
|---|---|---|
| `.env` | 本機金鑰 | 忽略 |
| `my-work/artifacts/api-test-2026-11-06/input-great-wave.jpg` | 測試圖（Met 公有領域） | 忽略 |
| `my-work/artifacts/api-test-2026-11-06/vision-error.json` | 403 錯誤原文 | 忽略 |
| `my-work/research/api-test-2026-11-06/run_api_test.py` | 可重跑的測試腳本 | 可 commit |
| `my-work/sources/processed/api-call-log-2026-11-06.md` | 呼叫紀錄（尚無成功呼叫，未建立） | 可 commit |
