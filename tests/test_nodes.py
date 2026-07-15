import asyncio
import types
from unittest.mock import AsyncMock, patch

import pytest

from src import nodes


class FakeVideoObject:
    def __init__(self, status, id="vid_1", error=None):
        self.status = status
        self.id = id
        self.error = error


@pytest.fixture(autouse=True)
def _hidden():
    nodes.APIVideoGenerate.hidden = types.SimpleNamespace(unique_id="test-node")
    yield
    nodes.APIVideoGenerate.hidden = None


def test_generate_success_polls_until_completed():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("processing"))
        status_mock = AsyncMock(
            side_effect=[FakeVideoObject("processing"), FakeVideoObject("completed")]
        )
        content_mock = AsyncMock(return_value=b"fake-mp4-bytes")

        with patch.object(nodes, "avideo_generation", gen_mock), patch.object(
            nodes, "avideo_status", status_mock
        ), patch.object(nodes, "avideo_content", content_mock), patch(
            "asyncio.sleep", AsyncMock(return_value=None)
        ):
            result = await nodes.APIVideoGenerate.execute(
                model="gemini/veo-3.1-fast-generate-preview",
                prompt="a cat riding a bike",
            )

        assert isinstance(result, nodes.io.NodeOutput)
        video = result.args[0]
        assert isinstance(video, nodes.InputImpl.VideoFromFile)
        assert video.file_obj.getvalue() == b"fake-mp4-bytes"
        assert status_mock.call_count == 2
        gen_mock.assert_awaited_once()
        assert "api_key" not in gen_mock.call_args.kwargs
        assert "api_key" not in status_mock.call_args.kwargs
        assert "api_key" not in content_mock.call_args.kwargs

    asyncio.run(run())


def test_api_key_threaded_through_every_call():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("completed"))
        status_mock = AsyncMock()
        content_mock = AsyncMock(return_value=b"bytes")

        with patch.object(nodes, "avideo_generation", gen_mock), patch.object(
            nodes, "avideo_status", status_mock
        ), patch.object(nodes, "avideo_content", content_mock), patch(
            "asyncio.sleep", AsyncMock(return_value=None)
        ):
            await nodes.APIVideoGenerate.execute(
                model="openai/sora-2",
                prompt="a dog surfing",
                api_key="sk-test-123",
            )

        assert gen_mock.call_args.kwargs["api_key"] == "sk-test-123"
        assert content_mock.call_args.kwargs["api_key"] == "sk-test-123"
        status_mock.assert_not_awaited()  # already completed, no polling needed

    asyncio.run(run())


def test_failed_generation_raises_runtime_error():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("processing"))
        status_mock = AsyncMock(
            return_value=FakeVideoObject("failed", error={"message": "content filtered"})
        )
        content_mock = AsyncMock()

        with patch.object(nodes, "avideo_generation", gen_mock), patch.object(
            nodes, "avideo_status", status_mock
        ), patch.object(nodes, "avideo_content", content_mock), patch(
            "asyncio.sleep", AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match="content filtered"):
                await nodes.APIVideoGenerate.execute(
                    model="gemini/veo-3.1-fast-generate-preview",
                    prompt="anything",
                )

        content_mock.assert_not_awaited()

    asyncio.run(run())


def test_timeout_raises_when_generation_never_completes():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("processing"))
        status_mock = AsyncMock(return_value=FakeVideoObject("processing"))

        with patch.object(nodes, "avideo_generation", gen_mock), patch.object(
            nodes, "avideo_status", status_mock
        ), patch("asyncio.sleep", AsyncMock(return_value=None)):
            with pytest.raises(TimeoutError):
                await nodes.APIVideoGenerate.execute(
                    model="gemini/veo-3.1-fast-generate-preview",
                    prompt="anything",
                    poll_interval=5.0,
                    timeout=12.0,
                )

    asyncio.run(run())
