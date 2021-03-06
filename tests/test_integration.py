# coding: utf-8
import coreapi
import requests
import pytest


encoded = (
    b'{"_type":"document","_meta":{"url":"http://example.org"},'
    b'"a":123,"next":{"_type":"link"}}'
)


@pytest.fixture
def document():
    return coreapi.load(encoded)


class MockResponse(object):
    def __init__(self, content):
        self.content = content
        self.headers = {}
        self.url = 'http://example.org'
        self.status_code = 200


# Basic integration tests.

def test_load():
    assert coreapi.load(encoded) == {
        "a": 123,
        "next": coreapi.Link(url='http://example.org')
    }


def test_dump(document):
    content_type, content = coreapi.dump(document)
    assert content_type == 'application/vnd.coreapi+json'
    assert content == encoded


def test_get(monkeypatch):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = coreapi.get('http://example.org')
    assert doc == {'example': 123}


def test_follow(monkeypatch, document):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = coreapi.action(document, ['next'])
    assert doc == {'example': 123}


def test_reload(monkeypatch):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = coreapi.Document(url='http://example.org')
    doc = coreapi.reload(doc)
    assert doc == {'example': 123}


def test_error(monkeypatch, document):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "error", "message": ["failed"]}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    with pytest.raises(coreapi.ErrorMessage):
        coreapi.action(document, ['next'])
