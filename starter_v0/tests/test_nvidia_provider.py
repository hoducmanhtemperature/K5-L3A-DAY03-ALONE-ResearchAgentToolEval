from types import SimpleNamespace as N

import pytest
import openai

from providers.nvidia_provider import NvidiaProvider


class Stream:
    def __init__(self, chunks):
        self.chunks = chunks
    def __enter__(self):
        return iter(self.chunks)
    def __exit__(self, *args):
        pass


def chunk(calls=None, text=None, finish=None):
    return N(choices=[N(delta=N(content=text, tool_calls=calls), finish_reason=finish)])


def fragment(index, name=None, args=None):
    return N(index=index, function=N(name=name, arguments=args))


def install(monkeypatch, chunks):
    observed = {}
    class Client:
        def __init__(self, **kwargs):
            observed['client'] = kwargs
            self.chat = N(completions=N(create=self.create))
        def create(self, **kwargs):
            observed['request'] = kwargs
            return Stream(chunks)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setenv('NVIDIA_API_KEY', 'test-key')
    monkeypatch.setattr(openai, 'OpenAI', Client)
    return observed


def test_stream_assembles_interleaved_calls_and_ignores_empty_choices(monkeypatch):
    observed = install(monkeypatch, [N(choices=[]), chunk([
        fragment(1, 'lookup', '{"query":'), fragment(0, 'timeline', '{"screen')]),
        chunk([fragment(0, args='name":"sama"}'), fragment(1, args='"AI"}')]),
        chunk(text='Done'), chunk(finish='tool_calls')])
    result = NvidiaProvider().complete([{'role': 'user', 'content': 'Research'}],
                                       tools=[{'type': 'function'}], tool_choice='required')
    assert [(x.name, x.args) for x in result.tool_calls] == [
        ('timeline', {'screenname': 'sama'}), ('lookup', {'query': 'AI'})]
    assert result.text == 'Done'
    assert observed['client']['base_url'] == 'https://integrate.api.nvidia.com/v1'
    req = observed['request']
    assert req['stream'] and req['parallel_tool_calls']
    assert req['seed'] == 42 and req['max_tokens'] == 16384
    assert req['extra_body'] == {'chat_template_kwargs': {'enable_thinking': True}}
    assert req['tool_choice'] == 'required'


@pytest.mark.parametrize('raw', ['{broken', '[]', 'null'])
def test_invalid_arguments_remain_observable_for_eval(raw, monkeypatch):
    install(monkeypatch, [chunk([fragment(0, 'lookup', raw)])])
    result = NvidiaProvider().complete([])
    assert result.tool_calls[0].args == {'_invalid_json_arguments': raw}


def test_missing_key_fails_before_request(monkeypatch):
    monkeypatch.delenv('NVIDIA_API_KEY', raising=False)
    with pytest.raises(RuntimeError, match='NVIDIA_API_KEY'):
        NvidiaProvider().complete([])


def test_truncated_response_is_not_executed(monkeypatch):
    install(monkeypatch, [chunk([fragment(0, 'send', '{')], finish='length')])
    with pytest.raises(RuntimeError, match='incomplete'):
        NvidiaProvider().complete([])
