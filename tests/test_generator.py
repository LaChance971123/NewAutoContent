from pipeline import generator

class DummyResp:
    def __init__(self, text: str, status: int = 200) -> None:
        self._text = text
        self.status_code = status

    def json(self) -> dict:
        return {"response": self._text}


def test_generate_story_basic(monkeypatch):
    def fake_post(url, json, timeout=30):
        return DummyResp("AI story")

    monkeypatch.setattr(generator, "requests", type("R", (), {"post": fake_post}))
    text = generator.generate_story(genre="fantasy", tone="exciting", prompt="The hero awakens")
    assert isinstance(text, str)
    assert text


def test_generate_story_fallback(monkeypatch):
    monkeypatch.setattr(generator, "requests", None)
    text = generator.generate_story(genre="horror", tone="dark")
    assert isinstance(text, str)
    assert "horror" in text
    assert "Once upon a time" in text
