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


def _gemini_source(model="veo-3.1-fast-generate-preview", **overrides):
    settings = {
        "model": model,
        "size": "16:9",
        "resolution": "1K",
        "seconds": 8,
        "person_generation": "allow_all",
    }
    settings.update(overrides)
    return {"source": "text", "provider": {"provider": "gemini", "model": settings}}


def _openai_source(model="sora-2", **overrides):
    settings = {"model": model, "size": "16:9", "resolution": "1K", "seconds": 4}
    settings.update(overrides)
    return {"source": "text", "provider": {"provider": "openai", "model": settings}}


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
                prompt="a cat riding a bike",
                source=_gemini_source(),
            )

        assert isinstance(result, nodes.io.NodeOutput)
        video = result.args[0]
        assert isinstance(video, nodes.InputImpl.VideoFromFile)
        assert video.file_obj.getvalue() == b"fake-mp4-bytes"
        assert status_mock.call_count == 2
        gen_mock.assert_awaited_once()
        assert gen_mock.call_args.kwargs["model"] == "gemini/veo-3.1-fast-generate-preview"
        assert gen_mock.call_args.kwargs["aspectRatio"] == "16:9"
        assert gen_mock.call_args.kwargs["resolution"] == "720p"
        assert gen_mock.call_args.kwargs["durationSeconds"] == 8
        assert gen_mock.call_args.kwargs["personGeneration"] == "allow_all"
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
                prompt="a dog surfing",
                source=_openai_source(),
                api_key="sk-test-123",
            )

        assert gen_mock.call_args.kwargs["model"] == "openai/sora-2"
        assert gen_mock.call_args.kwargs["size"] == "1280x720"
        assert gen_mock.call_args.kwargs["seconds"] == "4"
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
                    prompt="anything",
                    source=_gemini_source(),
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
                    prompt="anything",
                    source=_gemini_source(),
                    poll_interval=5.0,
                    timeout=12.0,
                )

    asyncio.run(run())


def test_runwayml_kwargs_mapping():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("completed"))
        content_mock = AsyncMock(return_value=b"bytes")

        source = {
            "source": "text",
            "provider": {
                "provider": "runwayml",
                "model": {
                    "model": "gen3a_turbo",
                    "size": "9:16",
                    "resolution": "2K",
                    "seconds": 10,
                    "seed": 42,
                },
            },
        }

        with patch.object(nodes, "avideo_generation", gen_mock), patch.object(
            nodes, "avideo_content", content_mock
        ), patch("asyncio.sleep", AsyncMock(return_value=None)):
            await nodes.APIVideoGenerate.execute(prompt="anything", source=source)

        assert gen_mock.call_args.kwargs["model"] == "runwayml/gen3a_turbo"
        assert gen_mock.call_args.kwargs["ratio"] == "1080:1920"
        assert gen_mock.call_args.kwargs["duration"] == 10
        assert gen_mock.call_args.kwargs["seed"] == 42

    asyncio.run(run())


def test_schema_builds_nested_source_provider_model_combo():
    schema = nodes.APIVideoGenerate.define_schema()
    source_input = next(i for i in schema.inputs if i.name == "source")
    assert [o.key for o in source_input.options] == ["text", "image"]

    text_option, image_option = source_input.options

    provider_input = text_option.inputs[0]
    assert provider_input.name == "provider"
    provider_keys = [o.key for o in provider_input.options]
    assert provider_keys == ["gemini", "openai", "azure", "runwayml"]

    for option in provider_input.options:
        model_input = option.inputs[0]
        assert model_input.name == "model"
        assert len(model_input.options) > 0
        for model_option in model_input.options:
            field_names = {i.name for i in model_option.inputs}
            assert {"size", "resolution", "seconds"} <= field_names

    image_provider_input = image_option.inputs[0]
    assert image_provider_input.name == "provider"
    assert [o.key for o in image_provider_input.options] == ["gemini"]

    gemini_model_input = image_provider_input.options[0].inputs[0]
    assert gemini_model_input.name == "model"
    for model_option in gemini_model_input.options:
        field_names = {i.name for i in model_option.inputs}
        assert {"size", "resolution", "seconds", "reference_image", "person_generation"} <= field_names

        person_generation_input = next(
            i for i in model_option.inputs if i.name == "person_generation"
        )
        assert person_generation_input.kwargs["options"] == ["allow_adult"]


def test_gemini_image_to_video_kwargs_mapping():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("completed"))
        content_mock = AsyncMock(return_value=b"bytes")

        fake_tensor = object()
        fake_bytesio = object()

        source = {
            "source": "image",
            "provider": {
                "provider": "gemini",
                "model": {
                    "model": "veo-3.1-fast-generate-preview",
                    "size": "9:16",
                    "resolution": "2K",
                    "seconds": 8,
                    "reference_image": fake_tensor,
                    "person_generation": "allow_adult",
                },
            },
        }

        with patch.object(nodes, "avideo_generation", gen_mock), patch.object(
            nodes, "avideo_content", content_mock
        ), patch.object(
            nodes.GeminiModel, "image_tensor_to_bytesio", return_value=fake_bytesio
        ) as tensor_mock, patch("asyncio.sleep", AsyncMock(return_value=None)):
            await nodes.APIVideoGenerate.execute(prompt="animate this photo", source=source)

        tensor_mock.assert_called_once_with(fake_tensor)
        kwargs = gen_mock.call_args.kwargs
        assert kwargs["model"] == "gemini/veo-3.1-fast-generate-preview"
        assert kwargs["aspectRatio"] == "9:16"
        assert kwargs["resolution"] == "1080p"
        assert kwargs["durationSeconds"] == 8
        assert kwargs["personGeneration"] == "allow_adult"
        assert kwargs["input_reference"] is fake_bytesio

    asyncio.run(run())


def test_gemini_image_to_video_requires_reference_image():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("completed"))

        source = {
            "source": "image",
            "provider": {
                "provider": "gemini",
                "model": {
                    "model": "veo-3.1-fast-generate-preview",
                    "size": "9:16",
                    "resolution": "2K",
                    "seconds": 8,
                    "person_generation": "allow_adult",
                },
            },
        }

        with patch.object(nodes, "avideo_generation", gen_mock):
            with pytest.raises(ValueError, match="reference_image"):
                await nodes.APIVideoGenerate.execute(prompt="animate this photo", source=source)

        gen_mock.assert_not_awaited()

    asyncio.run(run())


def test_azure_provider_string_uses_azure_prefix():
    async def run():
        gen_mock = AsyncMock(return_value=FakeVideoObject("completed"))
        content_mock = AsyncMock(return_value=b"bytes")

        source = _openai_source(model="sora-2-pro")
        source["provider"]["provider"] = "azure"

        with patch.object(nodes, "avideo_generation", gen_mock), patch.object(
            nodes, "avideo_content", content_mock
        ), patch("asyncio.sleep", AsyncMock(return_value=None)):
            await nodes.APIVideoGenerate.execute(prompt="anything", source=source)

        assert gen_mock.call_args.kwargs["model"] == "azure/sora-2-pro"

    asyncio.run(run())
