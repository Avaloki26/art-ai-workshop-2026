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
