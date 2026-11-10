# Tool Setup Guide

Use this guide before class. All keys go into `starter_v0/.env`. Never commit `.env`.

Pricing and quotas can change. The classroom target below is current for this lab setup as of 2026-06-02; re-check the provider page before a new cohort.

Smoke tests below call tools through the registry (`TOOL_FUNCTIONS`) so they only
verify that your API key works — they are not routing hints. Run them from `starter_v0/`.

## 1. Model Provider

Provider dùng cho bản hoàn thiện:

```bash
NVIDIA_API_KEY=...
NVIDIA_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
RESEARCH_UI_PASSWORD=...
```

NVIDIA dùng OpenAI SDK với `base_url=https://integrate.api.nvidia.com/v1`, streaming và parallel tool calls. `.env` được gitignore; không đưa key vào code hoặc transcript.

Preflight:

```bash
cd starter_v0
.venv/bin/python scripts/preflight_provider.py --provider nvidia
```

Local model (bonus Small Local Model Challenge, không cần API key):

```bash
# Cài Ollama: https://ollama.com/download
ollama pull qwen2.5:7b
python scripts/preflight_provider.py --provider ollama --model qwen2.5:7b
```

Tuỳ chọn trong `.env`: `OLLAMA_BASE_URL` (mặc định `http://localhost:11434/v1`), `OLLAMA_MODEL` (mặc định `qwen2.5:7b`).

## 2. Tavily — `lookup`

- Docs/credits: https://docs.tavily.com/documentation/api-credits
- API key page: https://app.tavily.com
- Classroom target: free plan with 1,000 API credits/month.

Setup:

1. Sign in at https://app.tavily.com.
2. Create or copy API key.
3. Add to `starter_v0/.env`:

```bash
TAVILY_API_KEY=tvly-...
```

Quick test:

```bash
python -c "from tools import TOOL_FUNCTIONS as T; print(T['lookup']('AI', max_results=1)['items'][0]['title'])"
```

## 3. Firecrawl — `fetch`

- Pricing: https://www.firecrawl.dev/pricing
- Docs: https://docs.firecrawl.dev
- Classroom target: free plan with 1,000 credits/month.

Setup:

1. Sign up at https://www.firecrawl.dev.
2. Create API key.
3. Add to `starter_v0/.env`:

```bash
FIRECRAWL_API_KEY=fc-...
```

Quick test:

```bash
python -c "from tools import TOOL_FUNCTIONS as T; print(T['fetch']('https://openai.com/research/')['items'][0]['title'])"
```

## 4. RapidAPI Twitter API45 — `timeline`, `social_search`

API đang dùng: [Twitter API45](https://rapidapi.com/alexanderxbx/api/twitter-api45).

1. Đăng nhập RapidAPI bằng tài khoản sở hữu key.
2. Mở tab **Pricing**, chọn gói phù hợp và hoàn tất **Subscribe**. Kiểm tra quyền gọi cả `timeline.php` và `search.php`; không giả định tài khoản đã có subscription chỉ vì đã có API key. Giá/quota xem trực tiếp ở Pricing.
3. Trong phần endpoint/code snippet, chọn đúng ứng dụng và copy `X-RapidAPI-Key` của ứng dụng đó vào `starter_v0/.env`. Key gắn với ứng dụng; xem [API Keys](https://docs.rapidapi.com/v2/docs/keys-and-key-rotation).
4. Giữ host đúng:

```bash
RAPIDAPI_KEY=...
RAPIDAPI_TWITTER_HOST=twitter-api45.p.rapidapi.com
```

5. Bấm **Test Endpoint** trên RapidAPI với `screenname=sama`; chỉ chạy eval sau khi endpoint hoạt động. Nếu vẫn 403 sau khi subscribe, đối chiếu tài khoản/ứng dụng, quyền của gói và code snippet; liên hệ API provider nếu quyền đã đúng.

Chẩn đoán từ `starter_v0/` (tự đọc `.env`, mỗi lệnh chỉ gọi một request, không cần NVIDIA):

```bash
.venv/bin/python -c "from pathlib import Path; from env_loader import load_lab_env; load_lab_env(Path.cwd()); from tools import TOOL_FUNCTIONS as T; r=T['timeline']('sama', limit=1); print({'error':r.get('error'), 'items':len(r.get('items', [])), 'message':r.get('message')})"
.venv/bin/python -c "from pathlib import Path; from env_loader import load_lab_env; load_lab_env(Path.cwd()); from tools import TOOL_FUNCTIONS as T; r=T['social_search']('AI', limit=1); print({'error':r.get('error'), 'items':len(r.get('items', [])), 'message':r.get('message')})"
```

Không chạy dồn các lệnh nếu tài khoản đang bị giới hạn. Các lệnh chỉ in lỗi, số item và thông báo; không in key. Kết quả có item và error=None cho biết tool đã lấy được dữ liệu.

- `403 / You are not subscribed to this API.`: subscription chưa cấp quyền cho request hiện tại; retry không giải quyết được quyền truy cập.
- `429 / Too many requests`: dừng request, xem **Subscriptions & Usage** và quota/rate limit. Chờ theo `Retry-After` nếu có; quota headers cho biết remaining/reset khi dịch vụ cung cấp. Không kết luận hết quota tháng chỉ từ thông báo này. Xem [Response Headers](https://docs.rapidapi.com/docs/response-headers) và [Subscription Plans](https://docs.rapidapi.com/v2/docs/api-pricing).

Khi cả hai lệnh kiểm tra đều thành công, chạy lại:

```bash
.venv/bin/python run_eval.py --provider nvidia --version v3 --suite base --eval-cases data/eval_base.json
```

## 5. arXiv Bonus — `papers`, `paper_text`

No API key is required. arXiv is rate-limited, so the tools wait between requests and retry lightly on HTTP 429.

Setup:

```bash
ARXIV_USER_AGENT=AI20k-Day03-Research-Agent/1.0 (your-team-name)
```

Quick tests:

```bash
python -c "from tools import TOOL_FUNCTIONS as T; print(T['papers']('AI agent evaluation', max_results=1)['items'][0]['title'])"
python -c "from tools import TOOL_FUNCTIONS as T; print(T['paper_text']('1706.03762', max_pages=1)['chars_returned'])"
```

Generated paper files go under `starter_v0/arxiv_papers/` and are ignored by git.

## 6. Telegram Bonus — `send`

Bonus action tool that posts text to a Telegram channel.

Official links:

- BotFather: https://t.me/BotFather
- Bot docs: https://core.telegram.org/bots

### Create Bot

1. Open Telegram.
2. Search for the official `@BotFather`.
3. Send:

```text
/newbot
```

4. Enter display name, for example:

```text
AI20k Research Bot
```

5. Enter username ending in `bot`, for example:

```text
ai20k_research_demo_bot
```

6. Copy the token BotFather returns.
7. Add to `starter_v0/.env`:

```bash
TELEGRAM_BOT_TOKEN=1234567890:AA....
```

Never paste this token into reports, screenshots, chat logs, or GitHub.

### Create Channel

1. Create a private Telegram channel.
2. Add your bot as admin.
3. Grant permission to post messages.

### Get Chat ID

For a public channel:

```bash
TELEGRAM_CHAT_ID=@your_channel_username
```

For a private channel:

1. Add bot as admin.
2. Post a fresh message in the channel.
3. Run:

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates"
```

4. Find:

```json
"chat": {"id": -1001234567890}
```

5. Add to `.env`:

```bash
TELEGRAM_CHAT_ID=-1001234567890
```

Direct tool test (verifies the bot token/chat only):

```bash
python -c "from tools import TOOL_FUNCTIONS as T; print(T['send']('AI20k test message', confirmed=True))"
```

## Final Checklist

Before class, at least one person per group should have:

- `NVIDIA_API_KEY`
- `TAVILY_API_KEY`
- `FIRECRAWL_API_KEY`
- `RAPIDAPI_KEY`
- optional `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- optional `ARXIV_USER_AGENT`
- `python scripts/preflight_provider.py --provider nvidia` passes
