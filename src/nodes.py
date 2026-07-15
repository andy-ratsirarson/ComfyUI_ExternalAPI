import asyncio
from io import BytesIO

from comfy_api.latest import ComfyAPI, InputImpl, io
from litellm import avideo_content, avideo_generation, avideo_status

api = ComfyAPI()

# litellm 1.92.0 implements video generation for these providers only.
# Update this note (and re-check litellm's llms/<provider>/videos/ dirs) as support grows.
SUPPORTED_PROVIDERS = "gemini, vertex_ai, runwayml, azure, openai"

_TERMINAL_STATUSES = ("completed", "failed")


class APIVideoGenerate(io.ComfyNode):
    """Text-to-video generation via litellm, using the caller's own provider API key (BYOK)."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="APIVideoGenerate",
            display_name="API Video Generate (BYOK)",
            category="external_api/video",
            description=(
                "Generates a video from a text prompt via litellm, using your own "
                f"provider API key. Providers litellm currently supports for video "
                f"generation: {SUPPORTED_PROVIDERS}."
            ),
            inputs=[
                io.String.Input(
                    "model",
                    default="gemini/veo-3.1-fast-generate-preview",
                    tooltip=(
                        "litellm 'provider/model' string, e.g. "
                        "gemini/veo-3.1-fast-generate-preview. Supported providers "
                        f"today: {SUPPORTED_PROVIDERS}."
                    ),
                ),
                io.String.Input(
                    "prompt",
                    multiline=True,
                    tooltip="Text description of the video to generate.",
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
    async def execute(cls, model, prompt, api_key="", poll_interval=10.0, timeout=600.0):
        node_id = cls.hidden.unique_id
        auth_kwargs = {"api_key": api_key} if api_key else {}

        op = await avideo_generation(model=model, prompt=prompt, timeout=timeout, **auth_kwargs)

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
