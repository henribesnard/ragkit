"""Gradio chatbot UI."""

from __future__ import annotations

import asyncio
import time

import gradio as gr

from ragkit.agents import AgentOrchestrator
from ragkit.config.schema import ChatbotConfig


def create_chatbot(config: ChatbotConfig, orchestrator: AgentOrchestrator) -> gr.Blocks:
    async def respond(message: str, history: list):
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

    async def respond_stream(message: str, history: list):
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

        chunk_size = 50
        partial = ""
        for idx in range(0, len(response), chunk_size):
            partial = response[: idx + chunk_size]
            yield partial
            await asyncio.sleep(0)

    handler = respond_stream if config.features.streaming else respond

    with gr.Blocks(theme=config.ui.theme, title=config.ui.title) as demo:
        gr.Markdown(f"# {config.ui.title}")
        gr.Markdown(config.ui.description)

        gr.ChatInterface(
            fn=handler,
            examples=config.ui.examples,
            textbox=gr.Textbox(placeholder=config.ui.placeholder),
        )

    return demo
