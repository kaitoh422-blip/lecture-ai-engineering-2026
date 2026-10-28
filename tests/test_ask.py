from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_token_usage_and_returns_response(monkeypatch, capsys):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=4,
        ),
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)

    result = ask_module.ask("question")

    assert result == "answer"
    assert "入力: 12, 出力: 4" in capsys.readouterr().out


def test_interactive_sends_multiple_questions_to_the_same_chat(monkeypatch, capsys):
    sent_questions = []

    def send_message(question):
        sent_questions.append(question)
        return SimpleNamespace(
            text=f"answer to {question}",
            usage_metadata=SimpleNamespace(
                prompt_token_count=12,
                candidates_token_count=4,
            ),
        )

    chat = SimpleNamespace(send_message=send_message)
    client = SimpleNamespace(
        chats=SimpleNamespace(create=lambda **kwargs: chat)
    )
    questions = iter(["first question", "follow-up", "/exit"])
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.interactive()

    assert sent_questions == ["first question", "follow-up"]
    assert "answer to follow-up" in capsys.readouterr().out