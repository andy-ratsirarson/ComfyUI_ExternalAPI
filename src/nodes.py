import asyncio
from io import BytesIO

from comfy_api.latest import ComfyAPI, InputImpl, io
from litellm import avideo_content, avideo_generation, avideo_status

from src.models.azure import AzureModel
from src.models.gemini import GeminiModel
from src.models.openai import OpenAIModel
from src.models.runwayml import RunwayMLModel

api = ComfyAPI()

_TERMINAL_STATUSES = ("completed", "failed")

_PROVIDERS = [GeminiModel, OpenAIModel, AzureModel, RunwayMLModel]
_PROVIDERS_BY_NAME = {p.PROVIDER: p for p in _PROVIDERS}

# Image-to-video is Gemini-only for now; other providers can be added here
# once they implement image_to_video_settings_inputs()/image_to_video_kwargs().
_IMAGE_TO_VIDEO_PROVIDERS = [GeminiModel]
_IMAGE_TO_VIDEO_PROVIDERS_BY_NAME = {p.PROVIDER: p for p in _IMAGE_TO_VIDEO_PROVIDERS}


class APIVideoGenerate(io.ComfyNode):
    """Text-to-video and image-to-video generation via litellm, using the caller's own provider API key (BYOK)."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="APIVideoGenerate",
            display_name="API Video Generate (BYOK)",
            category="external_api/video",
            description=(
                "Generates a video from a text prompt (or a text prompt plus a "
                "reference image) via litellm, using your own provider API key. "
                "Pick a source, provider, and model to reveal their parameters."
            ),
            inputs=[
                io.String.Input(
                    "prompt",
                    multiline=True,
                    tooltip="Text description of the video to generate.",
                ),
                io.DynamicCombo.Input(
                    "source",
                    options=[
                        io.DynamicCombo.Option(
                            "text",
                            [
                                io.DynamicCombo.Input(
                                    "provider",
                                    options=[
                                        p.model_combo_option(mode="text") for p in _PROVIDERS
                                    ],
                                    tooltip="Video generation provider.",
                                ),
                            ],
                        ),
                        io.DynamicCombo.Option(
                            "image",
                            [
                                io.DynamicCombo.Input(
                                    "provider",
                                    options=[
                                        p.model_combo_option(mode="image")
                                        for p in _IMAGE_TO_VIDEO_PROVIDERS
                                    ],
                                    tooltip="Image-to-video provider.",
                                ),
                            ],
                        ),
                    ],
                    tooltip="Generation source: a text prompt alone, or a text prompt plus a reference image.",
                ),
                io.String.Input(
                    "api_key",
                    default="",
                    optional=True,
                    tooltip=(
                        "Overrides the provider's standard env var (e.g. GEMINI_API_KEY, "
                        "OPENAI_API_KEY) when set. Warning: unlike an env var, this value "
                        "is saved into the workflow JSON and into output file metadata. "
                        "Prefer leaving this blank and setting the env var on the ComfyUI "
                        "server instead."
                    ),
                ),
                io.Float.Input(
                    "poll_interval",
                    default=10.0,
                    min=1.0,
                    optional=True,
                    tooltip="Seconds between status checks while the video is generating.",
                ),
                io.Float.Input(
                    "timeout",
                    default=600.0,
                    min=10.0,
                    optional=True,
                    tooltip="Maximum seconds to wait for generation before giving up.",
                ),
            ],
            outputs=[
                io.Video.Output(),
            ],
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    async def execute(cls, prompt, source, api_key="", poll_interval=10.0, timeout=600.0):
        node_id = cls.hidden.unique_id
        auth_kwargs = {"api_key": api_key} if api_key else {}

        source_mode = source["source"]
        provider_dict = source["provider"]
        provider_name = provider_dict["provider"]
        model_dict = provider_dict["model"]
        model_id = model_dict["model"]
        settings = {k: v for k, v in model_dict.items() if k != "model"}

        if source_mode == "text":
            provider_cls = _PROVIDERS_BY_NAME[provider_name]
            extra_kwargs = provider_cls.video_kwargs(model_id, settings)
        else:
            provider_cls = _IMAGE_TO_VIDEO_PROVIDERS_BY_NAME[provider_name]
            extra_kwargs = provider_cls.image_to_video_kwargs(model_id, settings)
        model = f"{provider_name}/{model_id}"

        op = await avideo_generation(
            model=model, prompt=prompt, timeout=timeout, **auth_kwargs, **extra_kwargs
        )

        elapsed = 0.0
        await api.execution.set_progress(0.0, timeout, node_id=node_id)
        while op.status not in _TERMINAL_STATUSES:
            if elapsed >= timeout:
                raise TimeoutError(f"Video generation timed out after {timeout}s")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            await api.execution.set_progress(min(elapsed, timeout), timeout, node_id=node_id)
            op = await avideo_status(video_id=op.id, timeout=timeout, **auth_kwargs)

        if op.status == "failed":
            raise RuntimeError(f"Video generation failed: {op.error}")

        video_bytes = await avideo_content(video_id=op.id, **auth_kwargs)
        await api.execution.set_progress(timeout, timeout, node_id=node_id)

        return io.NodeOutput(InputImpl.VideoFromFile(BytesIO(video_bytes)))


NODES = [APIVideoGenerate]
