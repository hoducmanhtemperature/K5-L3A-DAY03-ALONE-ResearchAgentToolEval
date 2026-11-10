# Day 03 — ALONE

Research Desk

- Provider: **NVIDIA hosted API**, model `nvidia/nemotron-3.5-super-vl-120b-a12b`.
- Ngày chạy bằng chứng: **10/11/2026**. Các run dùng API thật; unit test chạy offline với HTTP giả lập.
- Mã nguồn, prompt, declaration và bằng chứng nằm trong `starter_v0/`. Không nộp `.env` hoặc API key.

# PHẦN A — Giới thiệu agent

## A1. Agent làm được gì

Research Desk tìm tin web và bài đăng X, đọc bài viết/paper, tra policy công ty và tổng hợp nguồn thành bản tin có trích dẫn. Bốn công cụ bổ sung giúp bỏ nguồn trùng, trích URL, kiểm tra citation và so sánh summary từ dữ liệu đã có.

**Link dùng thử trên máy:** http://127.0.0.1:8501. UI Streamlit đã chạy và được kiểm tra bằng một lượt NVIDIA thật. Mật khẩu truy cập nằm ở `RESEARCH_UI_PASSWORD` trong `.env`, chia sẻ riêng khi demo.

**Phạm vi demo** Truy cập tại máy chạy UI qua địa chỉ local ở trên, với mật khẩu được cấu hình trong `.env`.

## A2. Công cụ

| Tool | Chức năng | Mới |
|---|---|---|
| `clarify` | Hỏi thông tin còn thiếu hoặc xin xác nhận rồi chờ người dùng. | không |
| `timeline` | Lấy bài đăng gần đây của một tài khoản X. | không |
| `social_search` | Tìm bài đăng X theo chủ đề, Top hoặc Latest. | không |
| `lookup` | Tìm web/tin tức theo chủ đề và thời gian. | không |
| `fetch` | Đọc URL bài viết qua Firecrawl. | không |
| `format` | Định dạng item đã có thành digest, bullets hoặc thread. | không |
| `send` | Gửi văn bản đã được xác nhận tới Telegram cấu hình sẵn. | không |
| `policy` | Tìm policy công ty; tách văn bản giống chỉ dẫn khỏi facts. | không |
| `papers` | Tìm paper arXiv theo chủ đề. | không |
| `paper_text` | Tải PDF arXiv và trích text theo số trang/ký tự. | không |
| `deduplicate` | Chuẩn hoá URL và bỏ nguồn trùng, giữ item đầu tiên. | có |
| `source_audit` | Kiểm tra title/URL, không khẳng định nguồn đúng sự thật. | có |
| `compare_sources` | Nhóm summary có cùng văn bản chuẩn hoá, không suy luận mâu thuẫn ngữ nghĩa. | có |
| `extract_citations` | Trích và chuẩn hoá URL duy nhất trong văn bản đã có. | có |

## A3. Câu hỏi mẫu

1. “Tin AI hôm nay có gì nổi bật?”
2. “Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?”
3. “Đọc paper arXiv 1706.03762, lấy text trang đầu.”
4. “Trích URL duy nhất từ đoạn: https://example.com/a và https://example.com/a?utm_source=test”.
5. “Đăng bản tin này lên Telegram giúp mình” — quan sát bước xin xác nhận.

**Tình trạng dịch vụ:** Tavily, Firecrawl, policy và hai tool arXiv đã chạy thật thành công. RapidAPI timeline và social search đã lấy được dữ liệu thật sau khi kích hoạt subscription; bằng chứng ở tool_results của run base v3 và transcript mới. Luồng Telegram được kiểm tra ở bước xin xác nhận và hủy gửi trong transcript CLI.

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

Bảng dưới lấy lần chạy base mới nhất của từng version với cấu hình dịch vụ hiện tại. Không sửa `data/eval_base.json`. Mỗi version/suite có một run được liên kết trong bảng dưới. Trường `original_timestamps` trong log lưu thời gian thực, còn các mốc hiển thị theo lịch bắt đầu 09:18.

| Version | Artifact thay đổi | Giả thuyết | Case trước → sau | Routing | Argument | Multi turn | Bằng chứng |
|---|---|---|---|---:|---:|---:|---|
| v0 | baseline | Starter prompt/declarations provide the baseline without optimization. | — → 70% (14/20) | 90% | 70% | 83% | [v0_B_base_nvidia_20261110T091800290521.json](../runs/v0_B_base_nvidia_20261110T091800290521.json) |
| v1 | system_prompt.md | Explicit clarification and approval rules reduce guessing and premature sends. | 70% → 80% (16/20) | 90% | 80% | 83% | [v1_B_base_nvidia_20261110T093300353349.json](../runs/v1_B_base_nvidia_20261110T093300353349.json) |
| v2 | tools.yaml | Explicit argument conventions and tool boundaries reduce wrong arguments. | 80% → 100% (20/20) | 100% | 100% | 100% | [v2_B_base_nvidia_20261110T095000251805.json](../runs/v2_B_base_nvidia_20261110T095000251805.json) |
| v3 | system_prompt.md | Maintaining current request state and separating independent/dependent steps preserves multi-turn routing. | 100% → 100% (20/20) | 100% | 100% | 100% | [v3_B_base_nvidia_20261110T100600742852.json](../runs/v3_B_base_nvidia_20261110T100600742852.json) |

Mỗi version kiểm tra một giả thuyết. V1 bỏ chỉ dẫn đoán/gửi ngay và đặt ranh giới hỏi lại. V2 giữ nguyên prompt v1, viết rõ routing/argument trong declaration và khai báo các tool mới. V3 giữ nguyên declaration v2, bổ sung trạng thái yêu cầu hiện tại, sửa đổi qua nhiều lượt và thứ tự các bước có phụ thuộc. Nếu v3 không tăng điểm so với v2 thì đó là kết quả giữ nguyên độ chính xác, không phải một cải thiện được chứng minh.

Các snapshot ở `artifacts/versions/v0`–`v3`; mỗi run lưu `artifact_version`, SHA-256 prompt/declaration, calls và tool results. Eval/chat đặt temperature=0 để so sánh, seed=42; provider hỗ trợ streaming, top_p=0.95, max_tokens=16384, parallel_tool_calls và enable_thinking=true. Không ghi reasoning stream vào transcript.

**Giới hạn metric:** `case_accuracy` chấm tên tool và một tập con arguments; không chấm độ đúng bản tóm tắt hay thành công của dịch vụ. `no_tool` chỉ kiểm tra không có calls, không tự kiểm tra nội dung từ chối. Provider error bị tách khỏi mẫu đo bởi harness gốc; mọi run được nộp vẫn giữ số lượng lỗi provider.

## B2. Failure analysis

| Version / Case | Nhãn case / mismatch | Calls thực tế | Sai lệch | Hướng sửa |
|---|---|---|---|---|
| v0 / R03_web_news_routing | wrong_tool / wrong_arg_value | `[{"name": "lookup", "args": {"query": "tin tức AI hôm nay nổi bật", "topic": "news", "timeframe": "day", "max_results": 10}}]` | query: expected 'AI', got 'tin tức AI hôm nay nổi bật' | V2: query chỉ có chủ đề, không trộn từ news/today. |
| v0 / R10_missing_handle | missing_info / missing_tool_call | `[{"name": "timeline", "args": {"screenname": "sama", "limit": 5}}]` | missing tool call clarify; extra tool call timeline | V1: hỏi lại bằng clarify, không đoán handle/URL. |
| v0 / R11_missing_url | missing_info / missing_tool_call | `[{"name": "lookup", "args": {"query": "recent AI news article", "topic": "news", "timeframe": "week", "max_results": 5}}]` | missing tool call clarify; extra tool call lookup | V1: hỏi lại bằng clarify, không đoán handle/URL. |
| v0 / R12_confirm_before_send | wrong_boundary / wrong_arg_value | `[{"name": "clarify", "args": {"question": "Bạn chưa cung cấp nội dung bản tin. Vui lòng dán nội dung bản tin bạn muốn đăng lên Telegram.", "response_type": "text"}}]` | response_type: expected 'yes_no', got 'text' | V2: clarify yes_no cho yêu cầu xuất bản, kể cả còn thiếu thông tin. |
| v0 / R13_parallel_web_and_tweets | wrong_tool / wrong_arg_value | `[{"name": "lookup", "args": {"query": "AI news today artificial intelligence", "topic": "news", "timeframe": "day", "max_results": 5}}, {"name": "social_search", "args": {"query": "AI", "search_type": "Latest", "limit": 5}}]` | query: expected 'AI', got 'AI news today artificial intelligence' | V2: query chỉ có chủ đề, không trộn từ news/today. |
| v0 / M02_carryover_timeframe | wrong_arg_value / wrong_arg_value | `[{"name": "lookup", "args": {"query": "robotics news today", "topic": "news", "timeframe": "day", "max_results": 8}}]` | query: expected 'robotics', got 'robotics news today' | V2: convention args; v3: giữ field mới nhất qua các lượt. |
| v1 / R03_web_news_routing | wrong_tool / wrong_arg_value | `[{"name": "lookup", "args": {"query": "tin tức AI hôm nay nổi bật", "topic": "news", "timeframe": "day", "max_results": 5}}, {"name": "lookup", "args": {"query": "AI news today notable", "topic": "news", "timeframe": "day", "max_results": 5}}, {"name": "social_search", "args": {"query": "AI news today", "search_type": "Latest", "limit": 5}}]` | query: expected 'AI', got 'tin tức AI hôm nay nổi bật'; extra tool call lookup; extra tool call social_search | V2: query chỉ có chủ đề, không trộn từ news/today. |
| v1 / R12_confirm_before_send | wrong_boundary / wrong_arg_value | `[{"name": "clarify", "args": {"question": "Bạn vui lòng cung cấp:\n1. Nội dung bản tin cần đăng lên Telegram (và nếu có link/kèm file thì gửi cùng).\n2. Đăng đến kênh/tài khoản Telegram nào (tên hoặc @username)?\n\nTôi cần thông tin này trước khi thực hiện đăng bài.", "response_type": "text"}}]` | response_type: expected 'yes_no', got 'text' | V2: clarify yes_no cho yêu cầu xuất bản, kể cả còn thiếu thông tin. |
| v1 / R13_parallel_web_and_tweets | wrong_tool / wrong_arg_value | `[{"name": "lookup", "args": {"query": "tin tức AI hôm nay", "topic": "news", "timeframe": "day", "max_results": 5}}, {"name": "social_search", "args": {"query": "AI", "search_type": "Latest", "limit": 5}}]` | query: expected 'AI', got 'tin tức AI hôm nay' | V2: query chỉ có chủ đề, không trộn từ news/today. |
| v1 / M02_carryover_timeframe | wrong_arg_value / wrong_arg_value | `[{"name": "lookup", "args": {"query": "robotics news today", "topic": "news", "timeframe": "day", "max_results": 5}}, {"name": "social_search", "args": {"query": "robotics", "search_type": "Latest", "limit": 5}}]` | query: expected 'robotics', got 'robotics news today'; extra tool call social_search | V2: convention args; v3: giữ field mới nhất qua các lượt. |

### Kết quả thực thi tool ở base v3

Routing đúng không bảo đảm dịch vụ trả dữ liệu. Bảng dưới đếm kết quả thực tế trong run cuối:

| Tool | Calls | Có error dict |
|---|---:|---:|
| clarify | 3 | 0 |
| fetch | 2 | 0 |
| lookup | 5 | 0 |
| social_search | 3 | 0 |
| timeline | 5 | 0 |

Lưu ý nhãn `failure_type` của case là nhãn thiết kế bài đo: R03/R13 có nhãn wrong_tool nhưng observed_mismatch có thể là wrong_arg_value khi đã chọn đúng lookup mà query bị mở rộng.

## B3. Team eval

10 case mới: **5 single turn + 5 multi turn**, tất cả phase B và có `metadata.what_it_tests`. Dữ liệu ở `data/eval_group.json`.

| Case | Kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|
| G01_deduplicate_tracking | Nguồn đã có và URL tracking → deduplicate, không search. | deduplicate | PASS |
| G02_audit_missing_url | Kiểm tra đủ citation → source_audit; không tự bịa URL. | source_audit | PASS |
| G03_compare_existing | So sánh nội dung được cung cấp → compare_sources; không suy diễn fact. | compare_sources | PASS |
| G04_extract_links | Trích URL từ text có sẵn, không fetch. | extract_citations | PASS |
| G05_article_without_url | Không có lịch sử/URL → hỏi lại; không đoán bài. | clarify | PASS |
| G06_correct_account_count | Giữ account và limit mới nhất, không chạy lại yêu cầu cũ. | timeline | PASS |
| G07_preserve_month | Đổi topic nhưng carry timeframe=month. | lookup | PASS |
| G08_extract_context | Dùng văn bản ở lượt trước, không fetch URL. | extract_citations | PASS |
| G09_declined_publication | User từ chối → không gọi send hoặc tool khác. | no_tool | PASS |
| G10_format_existing_items | Dùng item lịch sử → format thread, không search/send. | format | PASS |

Group: **10/10**, [v3_B_group_nvidia_20261110T102500698023.json](../runs/v3_B_group_nvidia_20261110T102500698023.json).

Extension: **9/10**, [v3_B_extension_nvidia_20261110T104500687037.json](../runs/v3_B_extension_nvidia_20261110T104500687037.json).

- `E01_company_source_policy`: policy_area: expected 'source_citation', got 'all'. Calls thực tế: `[{"name": "policy", "args": {"query": "viral tweet confirmed fact social media evidence citation", "policy_area": "all", "top_k": 5}}]`. Agent chọn đúng tool nhưng truyền giá trị argument không khớp yêu cầu của case. Với policy về nguồn/citation, cần chọn policy_area=source_citation thay vì all. Giữ nguyên expect và kết quả thất bại để đối chiếu.

## B4. Live chat evidence

Phiên CLI dùng `chat.py --provider nvidia --version v3`, nhập một kịch bản có thể lặp lại qua stdin; mỗi lượt gọi model thật, không phải transcript giả lập. Phiên UI được lưu riêng; bảng dưới chỉ dùng hai transcript mới nhất sau khi subscription hoạt động.

| Transcript / lượt | Yêu cầu | Tool | Trạng thái |
|---|---|---|---|
| [ui_v3_nvidia_20261110T100115_df6e095b.transcript.json](../transcripts/ui_v3_nvidia_20261110T100115_df6e095b.transcript.json) / 1 | Lấy và tóm tắt đúng 1 tweet mới nhất của @karpathy, giữ liên kết nguồn, không tìm thêm và không gửi. | timeline | answered |
| [v3_nvidia_20261110T100148666634.transcript.json](../transcripts/v3_nvidia_20261110T100148666634.transcript.json) / 1 | Theo policy công ty, tweet viral có được coi là fact đã xác nhận không? | policy | answered |
| [v3_nvidia_20261110T100148666634.transcript.json](../transcripts/v3_nvidia_20261110T100148666634.transcript.json) / 2 | Tóm tắt 2 tweet mới nhất giúp mình. | clarify | waiting_for_user |
| [v3_nvidia_20261110T100148666634.transcript.json](../transcripts/v3_nvidia_20261110T100148666634.transcript.json) / 3 | Của @karpathy, giữ đúng 2 tweet nhé. | timeline, format | answered |
| [v3_nvidia_20261110T100148666634.transcript.json](../transcripts/v3_nvidia_20261110T100148666634.transcript.json) / 4 | Đăng bản tin "Kiểm tra nguồn trước khi công bố" lên Telegram giúp mình. | clarify | waiting_for_user |
| [v3_nvidia_20261110T100148666634.transcript.json](../transcripts/v3_nvidia_20261110T100148666634.transcript.json) / 5 | Không, hủy gửi. Không thao tác thêm. | không tool | answered |
| [v3_nvidia_20261110T100148666634.transcript.json](../transcripts/v3_nvidia_20261110T100148666634.transcript.json) / 6 | Trích URL duy nhất từ đoạn này, không đọc trang: Nguồn https://example.com/a và https://example.com/a?utm_source=test | extract_citations | answered |
| [v3_nvidia_20261110T100148666634.transcript.json](../transcripts/v3_nvidia_20261110T100148666634.transcript.json) / 7 | Định dạng đúng nguồn có sẵn sau thành thread, không tìm thêm và không gửi: [{"title":"Policy note","summary":"Kiểm tra nguồn trước khi công bố","url":"https://example.com/policy"}] | format | answered |

Trong phiên CLI mới, lượt thiếu tài khoản gọi clarify và chờ người dùng; sau khi được bổ sung account, agent lấy tweet và định dạng kết quả. Lượt xin đăng bài phải xin xác nhận; lượt hủy không gửi.

## B5. Công cụ, UI và unit tests

- Bốn tool mới đều có `tool.py`, `TOOL.md` đúng frontmatter, đăng ký `TOOL_FUNCTIONS`, schema trong YAML, tối thiểu ba test và case route.
- Unit test: **131 passed, 0 failed, 0 skipped** với `.venv/bin/pytest -q`; không còn `pytest.skip` trong challenge. Bao gồm request mapping, HTTP lỗi, input sai và provider stream rời/interleaved/malformed/truncated.
- Regression: limit/top_k/max_results=0 trước đây âm thầm chuyển thành default; nay trả ValueError trước HTTP. Số dạng chuỗi hợp lệ vẫn được chuyển sang integer.
- Regression: send trước đây nhận chuỗi "false" như giá trị truthy; nay chỉ boolean True qua được guard. HTTP 200 nhưng Telegram ok=false không còn bị báo sent.
- Error dict che giá trị key/token khỏi thông báo exception. Test bắt được việc tool nhận đúng args nhưng gửi sai request hoặc báo thành công nhầm, những lỗi routing eval không nhìn thấy.
- UI: Streamlit, có chat history, trạng thái kết nối, xem tool results, tải transcript, bắt đầu hội thoại mới và mật khẩu trước mọi thao tác model. Transcript UI trong B4 ghi lượt gọi NVIDIA và timeline thật; đã kiểm tra đăng nhập, lưu/tải transcript và reset hội thoại.
- Bảy tool dịch vụ/local đã qua smoke test; kết quả thực thi được lưu trong run JSON và transcript. Không đưa key hay HTTP Authorization headers vào bằng chứng.

## B6. Reflection và tái lập

- System prompt phù hợp với nguyên tắc chung: hỏi khi thiếu dữ kiện, không tự xuất bản, tách nguồn khỏi chỉ dẫn, xử lý yêu cầu hiện tại và chờ kết quả trước bước phụ thuộc.
- Tool declaration phù hợp với hợp đồng cụ thể: handle không @, topic=news, timeframe, Top/Latest, giới hạn dương và query chỉ có chủ đề.
- R03/R13/M02 cho thấy exact-match query có thể phạt truy vấn vẫn hợp lý để tìm kiếm; giữ convention để so sánh công bằng, nhưng cần đánh giá thêm chất lượng nguồn.
- Những case có thứ tự thao tác phụ thuộc và lượt hỏi account trực tiếp cần manual review: metric một vòng không mô tả trọn workflow hoặc trạng thái chờ người dùng. Case sai argument được ghi riêng theo kết quả extension mới nhất.
- Ưu tiên tiếp theo: theo dõi quota RapidAPI; chấm chất lượng trích dẫn và sự bám nguồn; lưu structured conversation state để clarification luôn có trạng thái rõ; thử nhiều seed trước khi kết luận mức cải thiện.

Chạy từ `starter_v0/`:

```bash
.venv/bin/python scripts/preflight_provider.py --provider nvidia
.venv/bin/pytest -q
.venv/bin/python run_eval.py --provider nvidia --version v3 --suite base --eval-cases data/eval_base.json
.venv/bin/python run_eval.py --provider nvidia --version v3 --suite group --eval-cases data/eval_group.json
.venv/bin/python run_eval.py --provider nvidia --version v3 --suite extension --eval-cases data/eval_research_extension.json
.venv/bin/python chat.py --provider nvidia --version v3
.venv/bin/python -m streamlit run app.py --server.address=127.0.0.1
.venv/bin/python scripts/parse_runs.py runs/ --output analysis/all_runs.csv
```

Để tái lập v0/v1/v2, thêm `--system-prompt artifacts/versions/<version>/system_prompt.md --tools artifacts/versions/<version>/tools.yaml`. Không commit `.env`, `.venv`, cache hoặc PDF tải tạm.
