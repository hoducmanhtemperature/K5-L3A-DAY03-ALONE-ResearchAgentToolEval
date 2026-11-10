---
name: extract_citations
track: bonus
kind: local_formatter
provider: local
requires_env: []
inputs: [text]
outputs: [urls, count]
side_effect: false
---
# extract_citations

Trích URL HTTP(S) từ văn bản, chuẩn hoá và bỏ trùng. Không tải URL; dấu ngoặc cuối được coi là dấu phân cách.

Input sai trả về `error` và `message`; không raise ra agent. Chạy offline, không cần API key.
