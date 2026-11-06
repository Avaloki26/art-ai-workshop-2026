# 課堂提問與待確認事項

## 2026-11-06｜課前環境與目錄整合測試

> 本次沒有卡住超過 30 分鐘；以下是「已完成替代處理、但仍需本人確認」的項目。

### 1. Fork 與 remote 已設定完成

- 本地路徑：`/Users/kayiho/Documents/Default Project`
- 你的 fork（`origin`）：`https://github.com/Avaloki26/art-ai-workshop-2026.git`
- 官方倉庫（`upstream`）：`https://github.com/boan-anbo/art-ai-workshop-2026.git`
- 分支與基底版本：`main`，`2fea758`
- 已做：在 GitHub 建立 fork、把 `origin` 改成 fork、新增 `upstream`、完成 `git fetch --all`。
- 尚未做：還沒有把本地 commit push 到 GitHub（見第 3 點）。

### 2. Git 提交身分已設為 GitHub noreply

- 姓名：`Avaloki26`
- Email：`352713637+Avaloki26@users.noreply.github.com`
- 只寫在這個倉庫的 `.git/config`，沒有改動全域 Git 設定。
- 待確認：若你想用真實姓名或學校／個人 Email 署名，請告知；可在 push 前修改並 amend 第一個 commit。

### 3. 尚未設定 GitHub 推送憑證

- 現象：`git push --dry-run origin main` 回傳
  `remote: No anonymous write access.`
  `fatal: Authentication failed for 'https://github.com/Avaloki26/art-ai-workshop-2026.git/'`
- 原因：瀏覽器登入 GitHub 不等於命令列 Git 已授權；目前這台電腦沒有 `gh`（GitHub CLI），也沒有可用的 Git 憑證。
- 待確認：要用哪一種方式授權推送：
  1. 安裝 GitHub CLI（`brew install gh`）後執行 `gh auth login`；
  2. 使用 GitHub Desktop 登入並 push；
  3. 建立 Personal Access Token（PAT），存進 macOS Keychain（不要把 token 貼進對話）；
  4. 改用 SSH key（需先在 GitHub 加入公鑰）。

### 4. 預設 `git` 指向 `/usr/bin/git`，但缺少 Xcode Command Line Tools

- 錯誤訊息：`xcode-select: note: No developer tools were found, requesting install.`
- 目前可用的替代：`/opt/homebrew/bin/git --version` → `git version 2.56.0`
- 已做：只用 Homebrew 版 Git 檢查、clone、設定 remote 與 commit，未安裝 CLT、未重裝 Git。
- 待確認：是否要調整 `PATH` 讓 `/opt/homebrew/bin` 優先，或安裝 Xcode CLT（兩者都尚未執行）。
