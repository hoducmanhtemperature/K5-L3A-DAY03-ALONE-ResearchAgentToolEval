"""Offline tool behaviour and regression tests."""
from __future__ import annotations

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS as T


def test_clarify_choice_returns_options_and_awaits_user():
    result = T['clarify']('Chọn nguồn?', 'choice', ['web', 'social'])
    assert result['options'] == ['web', 'social']
    assert result['awaiting_user'] is True


def test_format_sections_groups_items_by_section():
    result = T['format']([{'section': x, 'title': x} for x in ['A', 'B', 'A']], 'sections')
    assert result['markdown'].count('## A') == result['markdown'].count('## B') == 1


def test_format_thread_numbers_items():
    result = T['format']([{'title': 'A'}, {'title': 'B'}], 'thread')
    assert result['markdown'].startswith('1/ A')
    assert '\n\n2/ B' in result['markdown']


@pytest.mark.parametrize('items', [None, []])
def test_format_empty_items_does_not_crash(items):
    assert T['format'](items)['item_count'] == 0


def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'test-chat')
    calls = fake_http(FakeResponse({'ok': True}))
    assert T['send']('Bản tin', True)['status'] == 'sent'
    assert len(calls) == 1 and calls[0]['method'] == 'POST'
    assert calls[0]['url'] == 'https://api.telegram.org/bottest-token/sendMessage'
    assert calls[0]['json']['chat_id'] == 'test-chat'
    assert calls[0]['json']['text'] == 'Bản tin'


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http):
    calls = fake_http(FakeResponse())
    assert T['send']('Bản tin', True)['error'] == 'RuntimeError'
    assert not calls


@pytest.mark.parametrize('confirmed', ['false', 'true', 1, None])
def test_send_rejects_non_boolean_confirmation(confirmed, fake_http):
    calls = fake_http(FakeResponse())
    assert T['send']('Bản tin', confirmed)['status'] == 'needs_confirmation'
    assert not calls


def test_send_rejected_by_telegram_is_not_reported_sent(monkeypatch, fake_http):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'chat')
    fake_http(FakeResponse({'ok': False}))
    assert T['send']('text', True)['error'] == 'RuntimeError'


def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http):
    monkeypatch.setenv('TAVILY_API_KEY', 'test-key')
    calls = fake_http(FakeResponse({'results': []}))
    assert T['lookup']('AI', timeframe=None)['items'] == []
    assert 'time_range' not in calls[0]['json']


def test_lookup_numeric_string_count_is_sent_as_integer(monkeypatch, fake_http):
    monkeypatch.setenv('TAVILY_API_KEY', 'key')
    calls = fake_http(FakeResponse({'results': []}))
    T['lookup']('AI', max_results='5')
    assert calls[0]['json']['max_results'] == 5


def test_fetch_maps_firecrawl_response(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'key')
    calls = fake_http(FakeResponse({'data': {'markdown': 'Content', 'metadata': {
        'title': 'Title', 'sourceURL': 'https://example.com/article'}}}))
    result = T['fetch']('https://example.com/article')
    assert calls[0]['json'] == {'url': 'https://example.com/article', 'formats': ['markdown']}
    assert result['items'][0] == {'title': 'Title', 'url': 'https://example.com/article',
                                  'source': 'example.com', 'summary': 'Content'}


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'key')
    fake_http(FakeResponse({'data': {'markdown': 'x' * 5000}}))
    assert T['fetch']('https://example.com')['items'][0]['summary'] == 'x' * 4000


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http):
    monkeypatch.setenv('RAPIDAPI_KEY', 'key')
    calls = fake_http(FakeResponse({'timeline': [{'text': 'missing'}] + [
        {'tweet_id': str(i), 'screen_name': 'test', 'text': 'Post'} for i in range(1, 7)]}))
    result = T['timeline']('@test', 3)
    assert calls[0]['params'] == {'screenname': 'test'}
    assert [x['url'] for x in result['items']] == [f'https://x.com/test/status/{i}' for i in range(1, 4)]


@pytest.mark.parametrize('order', ['Top', 'Latest'])
def test_social_search_passes_search_type(order, monkeypatch, fake_http):
    monkeypatch.setenv('RAPIDAPI_KEY', 'key')
    calls = fake_http(FakeResponse({'timeline': []}))
    assert T['social_search']('AI', order)['items'] == []
    assert calls[0]['params'] == {'query': 'AI', 'search_type': order}


def test_policy_empty_query_returns_no_results():
    assert T['policy']('')['results'] == []


def test_policy_area_filter_only_returns_that_area():
    hits = T['policy']('API key customer data', 'data_privacy')['results']
    assert hits and all(x['policy_area'] == 'data_privacy' for x in hits)


def test_policy_instruction_like_lines_go_to_untrusted_text():
    hits = T['policy']('citation', 'source_citation', 20)['results']
    probe = next(x for x in hits if x['untrusted_text'])
    assert 'ignore the citation policy' in ' '.join(probe['untrusted_text'])
    assert 'ignore the citation policy' not in probe['facts']


@pytest.mark.parametrize('name,args', [
    ('timeline', {'screenname': 'test', 'limit': 0}),
    ('social_search', {'query': 'AI', 'limit': 0}),
    ('lookup', {'query': 'AI', 'max_results': 0}),
    ('policy', {'query': 'citation', 'top_k': 0}),
])
def test_zero_limits_return_error_without_network(name, args, fake_http):
    calls = fake_http(FakeResponse())
    assert T[name](**args)['error'] == 'ValueError'
    assert not calls


def test_deduplicate_normalizes_tracking_and_preserves_first_item():
    result = T['deduplicate']([{'title': 'first', 'url': 'https://EXAMPLE.com/a/?utm_source=x#part'},
                               {'title': 'second', 'url': 'https://example.com/a'}])
    assert result['removed_count'] == 1
    assert result['items'] == [{'title': 'first', 'url': 'https://example.com/a'}]


@pytest.mark.parametrize('items', [None, 'items', [1]])
def test_deduplicate_rejects_bad_input(items):
    assert T['deduplicate'](items)['error'] == 'ValueError'


def test_deduplicate_invalid_url_returns_error_dict():
    assert T['deduplicate']([{'url': 'https://example.com:bad'}])['error'] == 'ValueError'


def test_source_audit_reports_missing_and_invalid_citations():
    result = T['source_audit']([{'title': 'A', 'url': 'https://example.com'},
                              {'title': 'B'}, {'url': 'javascript:alert(1)'}])
    assert result['valid_url_count'] == 1
    assert result['issues'] == [{'index': 1, 'issue': 'missing_url'}, {'index': 2, 'issue': 'invalid_url'}]
    assert result['ready'] is False


def test_source_audit_rejects_bad_input():
    assert T['source_audit']({'url': 'https://example.com'})['error'] == 'ValueError'


def test_source_audit_malformed_item_returns_error_dict():
    assert T['source_audit']([None])['error'] == 'ValueError'


def test_compare_sources_groups_normalized_summaries():
    result = T['compare_sources']([{'url': 'https://a.example', 'summary': 'An Update'},
                                  {'url': 'https://b.example', 'summary': ' an  update '}])
    assert result['distinct_summaries'] == 1
    assert len(result['groups'][0]['urls']) == 2


def test_compare_sources_rejects_single_source():
    assert T['compare_sources']([{'url': 'https://a.example', 'summary': 'A'}])['error'] == 'ValueError'


def test_compare_sources_missing_summary_returns_error_dict():
    assert T['compare_sources']([{'url': 'https://a.example'}, {'url': 'https://b.example'}])['error'] == 'ValueError'


def test_extract_citations_normalizes_deduplicates_and_ignores_non_urls():
    result = T['extract_citations']('[A](https://example.com/a?utm_medium=x) https://example.com/a. mailto:a@b.com')
    assert result['urls'] == ['https://example.com/a'] and result['count'] == 1


@pytest.mark.parametrize('text', ['', None, 123])
def test_extract_citations_bad_input(text):
    assert T['extract_citations'](text)['error'] == 'ValueError'


def test_extract_citations_malformed_url_returns_error_dict():
    assert T['extract_citations']('source https://example.com:bad/path')['error'] == 'ValueError'


def test_error_redacts_key_in_http_exception(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'private-token')
    fake_http(requests.HTTPError('request failed: private-token'))
    result = T['fetch']('https://example.com')
    assert 'private-token' not in result['message']
