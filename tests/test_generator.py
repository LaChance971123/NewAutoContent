from pipeline import generator


def test_generate_story_basic():
    text = generator.generate_story(genre="fantasy", tone="exciting", prompt="The hero awakens")
    assert isinstance(text, str)
    assert text
    assert "fantasy" in text
    assert "exciting" in text
    assert "The hero awakens" in text


def test_generate_story_fallback(monkeypatch):
    # Simulate OpenRouter failure by calling without prompt
    text = generator.generate_story(genre="horror", tone="dark")
    assert isinstance(text, str)
    assert "horror" in text
    assert "Once upon a time" in text
