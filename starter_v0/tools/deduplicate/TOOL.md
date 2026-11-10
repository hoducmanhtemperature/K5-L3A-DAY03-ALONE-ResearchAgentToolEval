---
name: deduplicate
track: bonus
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [items, removed_count]
side_effect: false
---
# deduplicate

Bỏ URL trùng, fragment và tracking parameters từ item đã có. Giữ item đầu tiên. Không tải trang hay tìm tin mới.

Input sai trả về `error` và `message`; không raise ra agent. Chạy offline, không cần API key.
