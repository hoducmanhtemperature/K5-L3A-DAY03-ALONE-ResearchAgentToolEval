from __future__ import annotations

import os
import hmac
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import now_iso, run_model_tool_loop, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).resolve().parent
load_lab_env(ROOT)
st.set_page_config(page_title='Research Desk', page_icon='📚', layout='wide')
# Authenticate before rendering tools, history, or invoking any service.
password = os.getenv('RESEARCH_UI_PASSWORD')
if password and not st.session_state.get('authenticated'):
    st.title('Research Desk')
    with st.form('login'):
        entered = st.text_input('Mật khẩu truy cập', type='password')
        submitted = st.form_submit_button('Đăng nhập')
    if submitted:
        if hmac.compare_digest(entered.encode(), password.encode()):
            st.session_state.authenticated = True
            st.rerun()
        st.error('Mật khẩu chưa đúng.')
    st.stop()

st.title('Research Desk')
st.caption('Tìm nguồn, đọc tài liệu và chuẩn bị bản tin có trích dẫn.')

with st.sidebar:
    st.subheader('Kết nối')
    st.write('NVIDIA · Nemotron 3.5 Super VL')
    for label, key in [('Model', 'NVIDIA_API_KEY'), ('Web', 'TAVILY_API_KEY'),
                       ('Đọc URL', 'FIRECRAWL_API_KEY'), ('Twitter / X', 'RAPIDAPI_KEY')]:
        st.write(f'{"✓" if os.getenv(key) else "○"} {label}')
    st.caption('Các công cụ xử lý nguồn và tra policy hoạt động không cần key dịch vụ ngoài.')
    if st.button('Cuộc trò chuyện mới'):
        for name in ('history', 'transcript', 'transcript_path'):
            st.session_state.pop(name, None)
        st.rerun()

prompt_path = ROOT / 'artifacts/system_prompt.md'
tools_path = ROOT / 'artifacts/tools.yaml'
if 'history' not in st.session_state:
    stamp = datetime.now().strftime('%Y%m%dT%H%M%S') + '_' + uuid.uuid4().hex[:8]
    st.session_state.history = []
    st.session_state.transcript_path = ROOT / 'transcripts' / f'ui_v3_nvidia_{stamp}.transcript.json'
    st.session_state.transcript = {
        'transcript_id': f'ui_v3_nvidia_{stamp}',
        **artifact_version_dict(build_artifact_version('v3', prompt_path, tools_path)),
        'provider': 'nvidia', 'model': make_provider('nvidia').default_model,
        'created_at': now_iso(), 'turns': [],
    }

if not st.session_state.history:
    st.info('Thử: “Theo policy công ty, tweet viral có được xem là fact đã xác nhận không?”')
    with st.expander('Các công cụ có sẵn'):
        for tool in load_tool_declarations(tools_path):
            st.markdown(f'**{tool["name"]}** — {tool["description"]}')

for message in st.session_state.history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_text = st.chat_input('Bạn muốn nghiên cứu điều gì?')
if user_text:
    with st.chat_message('user'):
        st.markdown(user_text)
    turn = {'turn_index': len(st.session_state.transcript['turns']) + 1,
            'user': user_text, 'started_at': now_iso()}
    with st.chat_message('assistant'):
        try:
            with st.spinner('Đang xử lý yêu cầu…'):
                result = run_model_tool_loop(
                    provider=make_provider('nvidia'),
                    messages=[{'role': 'system', 'content': prompt_path.read_text()},
                              *trim_history(st.session_state.history, 5),
                              {'role': 'user', 'content': user_text}],
                    tools=to_openai_tools(load_tool_declarations(tools_path)),
                    model=None, max_tool_rounds=5,
                )
            turn.update(result)
            st.markdown(result['assistant_text'])
            if result['tool_events']:
                with st.expander('Nguồn và kết quả công cụ'):
                    st.json(result['tool_events'])
        except Exception as exc:
            turn.update(status='provider_error', error=type(exc).__name__,
                        assistant_text='Chưa kết nối được dịch vụ. Kiểm tra cấu hình hoặc thử lại.')
            st.error(turn['assistant_text'])
    st.session_state.history += [{'role': 'user', 'content': user_text},
                                 {'role': 'assistant', 'content': turn['assistant_text']}]
    turn['ended_at'] = now_iso()
    st.session_state.transcript['turns'].append(turn)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)

if st.session_state.transcript['turns']:
    import json
    st.download_button('Tải transcript JSON',
                       json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2),
                       file_name=st.session_state.transcript_path.name, mime='application/json')
