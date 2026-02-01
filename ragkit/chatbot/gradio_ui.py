"""Gradio chatbot UI."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import gradio as gr

from ragkit.agents import AgentOrchestrator
from ragkit.config.schema import ChatbotConfig


def create_chatbot(config: ChatbotConfig, orchestrator: AgentOrchestrator) -> gr.Blocks:
    async def respond(message: str, history: list) -> str:
        start = time.perf_counter()
        result = await orchestrator.process(message, history)
        response = result.response.content

        if config.features.show_sources and result.response.sources:
            response += "\n\nSources:\n"
            for source in result.response.sources:
                response += f"- {source}\n"

        if config.features.show_latency:
            latency = time.perf_counter() - start
            response += f"\n\nLatency: {latency:.2f}s"

        return response

    async def respond_stream(message: str, history: list) -> AsyncIterator[str]:
        start = time.perf_counter()
        partial = ""
        async for event in orchestrator.process_stream(message, history):
            event_type = event.get("type")
            if event_type == "delta":
                partial += event.get("content", "")
                yield partial
            elif event_type == "final":
                response = event.get("content", "")
                sources = event.get("sources", []) or []
                if config.features.show_sources and sources:
                    response += "\n\nSources:\n"
                    for source in sources:
                        response += f"- {source}\n"
                if config.features.show_latency:
                    latency = time.perf_counter() - start
                    response += f"\n\nLatency: {latency:.2f}s"
                yield response
            elif event_type == "error":
                message = event.get("message", "Streaming error")
                yield f"Error: {message}"

    handler = respond_stream if config.features.streaming else respond

    with gr.Blocks() as demo:
        gr.Markdown(f"# {config.ui.title}")
        gr.Markdown(config.ui.description)

        gr.ChatInterface(
            fn=handler,
            examples=config.ui.examples,
            textbox=gr.Textbox(placeholder=config.ui.placeholder),
        )

    return demo
