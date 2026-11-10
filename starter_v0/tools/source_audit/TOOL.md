---
name: source_audit
track: bonus
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [issues, ready, valid_url_count]
side_effect: false
---
# source_audit

Kiểm tra item đã có có title và URL hợp lệ. Không xác minh nội dung, uy tín hay tính đúng của nguồn.

Input sai trả về `error` và `message`; không raise ra agent. Chạy offline, không cần API key.
