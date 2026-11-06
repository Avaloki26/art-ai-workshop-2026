#!/usr/bin/env python3
"""
OpenRouter 最小整合測試：視覺／OCR + 圖文 Embedding
=====================================================

用途
----
1. 從本機 `.env` 讀取 OPENROUTER_API_KEY（不寫死、不印出、不進 Git）。
2. `--vision`    ：用一張公有領域圖片跑一次「看圖 + 轉錄文字」。
3. `--embedding` ：把同一張圖與幾句文字轉成向量，計算餘弦相似度。
4. 把完整 API 回應存進 `my-work/artifacts/api-test-2026-11-06/`。
5. 把模型、日期、token、費用寫成 `my-work/sources/processed/api-call-log-2026-11-06.md`。

用法（在倉庫根目錄執行）
------------------------
    python3 my-work/research/api-test-2026-11-06/run_api_test.py --check-key
    python3 my-work/research/api-test-2026-11-06/run_api_test.py --vision
    python3 my-work/research/api-test-2026-11-06/run_api_test.py --embedding
    python3 my-work/research/api-test-2026-11-06/run_api_test.py --all

地區限制備註（2026-11-06 實測）
-------------------------------
從香港網路呼叫 `google/gemini-3.1-flash-lite` 會得到 HTTP 403
「This model is not available in your region.」，請求未計費。
若要在本地區測試，改用供應商有在亞洲服務的模型，例如：

    --vision-model qwen/qwen3-vl-30b-a3b-instruct   # $0.15/M in, $0.60/M out

本檔預設值仍保留原提案的 Gemini，需以參數覆寫。

設計原則
--------
- 只做一次呼叫；失敗就把錯誤原文存檔後停止，不自動重試（避免重複計費）。
- 任何輸出都不含 API Key。
- 費用以 API 回傳的 usage.cost 為準；若缺少才用價目表估算。
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------- 路徑與常數

REPO_ROOT = Path.cwd()
ENV_PATH = REPO_ROOT / ".env"
ARTIFACT_DIR = REPO_ROOT / "my-work" / "artifacts" / "api-test-2026-11-06"
RECORD_PATH = REPO_ROOT / "my-work" / "sources" / "processed" / "api-call-log-2026-11-06.md"
INPUT_IMAGE = ARTIFACT_DIR / "input-great-wave.jpg"

API_BASE = "https://openrouter.ai/api/v1"

VISION_MODEL = "google/gemini-3.1-flash-lite"
EMBEDDING_MODEL = "cohere/embed-5-fast"

# 台北時間，方便和課堂紀錄對照
TZ = timezone(timedelta(hours=8))


# ---------------------------------------------------------------- 小工具


def die(message: str, code: int = 1) -> None:
    print(f"\n[停止] {message}", file=sys.stderr)
    sys.exit(code)


def read_api_key() -> str:
    """只從 .env 讀取金鑰；不從命令列參數或環境變數以外的來源拿。"""
    if not ENV_PATH.exists():
        die(f"找不到 {ENV_PATH}，請先建立 .env 並填入 OPENROUTER_API_KEY")

    key = None
    for line in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s.startswith("OPENROUTER_API_KEY="):
            key = s.split("=", 1)[1].strip().strip('"').strip("'")

    if not key:
        die("`.env` 裡的 OPENROUTER_API_KEY 是空的；請貼上金鑰後存檔再執行")
    if not key.startswith("sk-or-v1-"):
        die("金鑰前綴不是 `sk-or-v1-`，可能貼錯內容（未印出金鑰以免外洩）")
    return key


def api_request(path: str, payload: dict, key: str, timeout: int = 180) -> dict:
    """送一個 JSON POST，回傳解析後的 JSON。錯誤時保留原始回應本文。"""
    url = f"{API_BASE}{path}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # OpenRouter 用來在網頁上標示來源，可留空
            "HTTP-Referer": "https://github.com/Avaloki26/art-ai-workshop-2026",
            "X-Title": "Art AI Workshop API integration test",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {raw}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"連線失敗: {e.reason}") from None


def api_get(path: str, key: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        method="GET",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {raw}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"連線失敗: {e.reason}") from None


def image_data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "jpeg"
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def save_json(name: str, data: dict) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACT_DIR / name
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def now_tw() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def usd(x: float | None) -> str:
    if x is None:
        return "未回報"
    return f"${x:.6f}"


def append_record(section: str, lines: list[str]) -> None:
    RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# OpenRouter 呼叫紀錄（2026-11-06）\n\n"
        "> 每次呼叫只做一次；費用取自 API 回應的 `usage.cost`（美元）。\n"
        "> 金鑰只存在本機 `.env`，未寫入本檔或任何 commit。\n\n"
    )
    if not RECORD_PATH.exists():
        RECORD_PATH.write_text(header, encoding="utf-8")
    with RECORD_PATH.open("a", encoding="utf-8") as f:
        f.write("\n" + section + "\n\n" + "\n".join(lines) + "\n")


# ---------------------------------------------------------------- 檢查金鑰


def check_key(key: str) -> None:
    """只顯示額度與用量，不顯示金鑰本身。"""
    info = api_get("/key", key)
    d = info.get("data", info)
    print("金鑰有效。以下為帳戶額度資訊（不含金鑰）：")
    for k in ("label", "usage", "limit", "limit_remaining", "is_free_tier", "rate_limit"):
        if k in d:
            print(f"  {k:16}: {d[k]}")


# ---------------------------------------------------------------- 測試 1：視覺／OCR


VISION_PROMPT = (
    "You are helping an art-history workshop test a vision model. "
    "Look at the image and answer in English, concisely:\n"
    "1) Describe what is depicted in 3-4 sentences (subject, composition, colours, style).\n"
    "2) Transcribe any visible written text exactly as it appears, including seals or signatures. "
    "If a character is unclear, write [?] instead of guessing.\n"
    "3) State the writing system/language of the text if you can identify it.\n"
    "Do not invent details that are not visible."
)


def run_vision(key: str) -> None:
    if not INPUT_IMAGE.exists():
        die(f"找不到測試圖片 {INPUT_IMAGE}")

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data_url(INPUT_IMAGE)}},
                ],
            }
        ],
        "max_tokens": 900,
        "temperature": 0,
    }

    print(f"[1/2] 視覺／OCR：{VISION_MODEL}")
    print("      測試圖：Met Museum 公有領域《神奈川沖浪裏》(600×403 JPEG)")
    try:
        resp = api_request("/chat/completions", payload, key)
    except RuntimeError as e:
        save_json("vision-error.json", {"error": str(e), "time": now_tw()})
        die(f"視覺呼叫失敗（已存到 artifacts/vision-error.json）：{e}")

    save_json("vision-response.json", resp)

    msg = (resp.get("choices") or [{}])[0].get("message", {}) or {}
    answer = msg.get("content") or ""
    text_out = ARTIFACT_DIR / "vision-answer.md"
    text_out.write_text(answer, encoding="utf-8")

    usage = resp.get("usage") or {}
    cost = usage.get("cost")
    print("\n----- 模型回應 -----")
    print(answer)
    print("--------------------")
    print(f"prompt_tokens={usage.get('prompt_tokens')} completion_tokens={usage.get('completion_tokens')} cost={usd(cost)}")

    append_record(
        "## 1. 視覺／OCR（圖像描述 + 文字轉錄）",
        [
            f"- 時間：{now_tw()}",
            f"- 模型：`{VISION_MODEL}`（{resp.get('model', VISION_MODEL)}）",
            f"- 輸入：`my-work/artifacts/api-test-2026-11-06/input-great-wave.jpg`",
            "- 輸入來源：The Metropolitan Museum of Art, object 45434，公有領域（CC0）",
            "- 輸入尺寸：600×403 JPEG",
            "- 參數：`temperature=0`, `max_tokens=900`",
            f"- 用量：prompt_tokens={usage.get('prompt_tokens')}, completion_tokens={usage.get('completion_tokens')}, total_tokens={usage.get('total_tokens')}",
            f"- 費用（API 回報）：**{usd(cost)}**",
            f"- 完整回應：`my-work/artifacts/api-test-2026-11-06/vision-response.json`",
            f"- 純文字輸出：`my-work/artifacts/api-test-2026-11-06/vision-answer.md`",
            f"- response id：`{resp.get('id')}`",
        ],
    )
    print(f"      已存檔：{text_out.name} / vision-response.json")


# ---------------------------------------------------------------- 測試 2：圖文 Embedding


TEXT_CANDIDATES = [
    ("A", "A Japanese ukiyo-e woodblock print of a huge wave curling over small boats, "
          "with Mount Fuji visible in the distance."),
    ("B", "A still-life oil painting of cut flowers in a glass vase on a wooden table."),
    ("C", "A night-time photograph of a modern city skyline with lit skyscrapers."),
    ("D", "A diagram explaining the water cycle: evaporation, condensation and rain."),
]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def run_embedding(key: str) -> None:
    if not INPUT_IMAGE.exists():
        die(f"找不到測試圖片 {INPUT_IMAGE}")

    inputs = [{"content": [{"type": "image_url", "image_url": {"url": image_data_url(INPUT_IMAGE)}}]}]
    for _, text in TEXT_CANDIDATES:
        inputs.append({"content": [{"type": "text", "text": text}]})

    payload = {"model": EMBEDDING_MODEL, "input": inputs, "encoding_format": "float"}

    print(f"\n[2/2] 圖文 Embedding：{EMBEDDING_MODEL}")
    print("      比較：1 張圖 vs 4 句文字描述，計算餘弦相似度")
    try:
        resp = api_request("/embeddings", payload, key)
    except RuntimeError as e:
        save_json("embedding-error.json", {"error": str(e), "time": now_tw()})
        die(f"Embedding 呼叫失敗（已存到 artifacts/embedding-error.json）：{e}")

    save_json("embedding-response.json", resp)

    vectors = [d.get("embedding") for d in resp.get("data", [])]
    if len(vectors) != 5 or any(not isinstance(v, list) for v in vectors):
        save_json("embedding-unexpected.json", resp)
        die("Embedding 回應格式與預期不同（已存 embedding-unexpected.json）")

    img_vec = vectors[0]
    rows = []
    for i, (label, text) in enumerate(TEXT_CANDIDATES, start=1):
        rows.append((label, text, cosine(img_vec, vectors[i])))
    rows.sort(key=lambda r: r[2], reverse=True)

    usage = resp.get("usage") or {}
    cost = usage.get("cost")
    dims = len(img_vec)

    lines_md = [
        "| 排名 | 候選 | 餘弦相似度 | 文字 |",
        "|---|---|---|---|",
    ]
    for rank, (label, text, score) in enumerate(rows, start=1):
        lines_md.append(f"| {rank} | {label} | {score:.4f} | {text} |")

    table = "\n".join(lines_md)
    print("\n----- 相似度（1.0 = 完全相同語義）-----")
    print(table)
    print("--------------------------------------")
    print(f"向量維度={dims} prompt_tokens={usage.get('prompt_tokens')} "
          f"image_tokens={(usage.get('prompt_tokens_details') or {}).get('image_tokens')} cost={usd(cost)}")

    out_md = ARTIFACT_DIR / "embedding-similarity.md"
    out_md.write_text(
        f"# 圖文 Embedding 相似度\n\n- 模型：`{EMBEDDING_MODEL}`\n- 時間：{now_tw()}\n"
        f"- 圖片：`input-great-wave.jpg`\n- 向量維度：{dims}\n\n{table}\n",
        encoding="utf-8",
    )

    append_record(
        "## 2. 圖文 Embedding（語義檢索相似度）",
        [
            f"- 時間：{now_tw()}",
            f"- 模型：`{EMBEDDING_MODEL}`（{resp.get('model', EMBEDDING_MODEL)}）",
            f"- 輸入：1 張圖（`input-great-wave.jpg`）+ 4 句英文描述",
            f"- 參數：`encoding_format=float`；向量維度 {dims}",
            f"- 用量：prompt_tokens={usage.get('prompt_tokens')}, "
            f"image_tokens={(usage.get('prompt_tokens_details') or {}).get('image_tokens')}, "
            f"total_tokens={usage.get('total_tokens')}",
            f"- 費用（API 回報）：**{usd(cost)}**",
            "",
            table,
            "",
            f"- 完整回應（含向量）：`my-work/artifacts/api-test-2026-11-06/embedding-response.json`",
            f"- 相似度表：`my-work/artifacts/api-test-2026-11-06/embedding-similarity.md`",
            f"- response id：`{resp.get('id')}`",
        ],
    )
    print(f"      已存檔：{out_md.name} / embedding-response.json")


# ---------------------------------------------------------------- 主程式


def main() -> None:
    ap = argparse.ArgumentParser(description="OpenRouter minimal integration test")
    ap.add_argument("--check-key", action="store_true", help="只檢查金鑰與額度")
    ap.add_argument("--vision", action="store_true", help="執行視覺／OCR 測試")
    ap.add_argument("--embedding", action="store_true", help="執行圖文 embedding 測試")
    ap.add_argument("--all", action="store_true", help="兩個測試都執行")
    ap.add_argument("--vision-model", default=VISION_MODEL,
                    help=f"覆寫視覺模型（預設 {VISION_MODEL}）")
    ap.add_argument("--embedding-model", default=EMBEDDING_MODEL,
                    help=f"覆寫 embedding 模型（預設 {EMBEDDING_MODEL}）")
    args = ap.parse_args()

    global VISION_MODEL, EMBEDDING_MODEL
    VISION_MODEL = args.vision_model
    EMBEDDING_MODEL = args.embedding_model

    if not any([args.check_key, args.vision, args.embedding, args.all]):
        ap.print_help()
        return

    key = read_api_key()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    if args.check_key:
        check_key(key)
    if args.all or args.vision:
        run_vision(key)
    if args.all or args.embedding:
        run_embedding(key)


if __name__ == "__main__":
    main()
