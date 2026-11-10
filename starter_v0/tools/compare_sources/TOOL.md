---
name: compare_sources
track: bonus
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [groups, distinct_summaries]
side_effect: false
---
# compare_sources

Nhóm summary giống nhau sau khi chuẩn hoá chữ và khoảng trắng. Cần ít nhất hai nguồn; không suy diễn mâu thuẫn ngữ nghĩa.

Input sai trả về `error` và `message`; không raise ra agent. Chạy offline, không cần API key.
