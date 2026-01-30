import pytest

gradio = pytest.importorskip("gradio")

from ragkit.chatbot.gradio_ui import create_chatbot
from ragkit.config.schema import ChatbotConfig, ChatbotFeaturesConfig, ChatbotServerConfig, ChatbotUIConfig


class DummyOrchestrator:
    async def process(self, query, history=None):
        class Result:
            def __init__(self):
                self.response = type("Resp", (), {"content": "Hi", "sources": []})()

        return Result()


def test_chatbot_creation():
    config = ChatbotConfig(
        enabled=True,
        type="gradio",
        server=ChatbotServerConfig(host="0.0.0.0", port=8080, share=False),
        ui=ChatbotUIConfig(title="RAGKIT", description="Desc", theme="soft", placeholder="Ask", examples=[]),
        features=ChatbotFeaturesConfig(show_sources=True, show_latency=True),
    )
    demo = create_chatbot(config, DummyOrchestrator())
    assert demo is not None
