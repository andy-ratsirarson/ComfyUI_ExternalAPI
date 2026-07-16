from src.models.base import Model
from src.settings.base import Resolutions, Sizes
from src.settings.video import VideoSettings, dimensions_string


class _SoraModel(Model):
    """Shared Sora video logic for the OpenAI and Azure providers, which expose
    the same model family and parameters via litellm. Subclasses set PROVIDER."""

    # MAX_SECONDS=12 is a reasonable-but-unconfirmed ceiling: litellm's own
    # default is "4" and no hard max was confirmed against Sora's API docs.
    VIDEO_SETTINGS = VideoSettings(
        SIZE=[Sizes._16_9, Sizes._9_16],
        RESOLUTIONS=[Resolutions._1K, Resolutions._2K],
        MIN_SECONDS=4,
        MAX_SECONDS=12,
    )

    @classmethod
    def list_models(cls) -> list[str]:
        return ["sora-2", "sora-2-pro", "sora-2-pro-high-res"]

    @classmethod
    def video_kwargs(cls, model_id: str, settings: dict) -> dict:
        size = dimensions_string(settings["size"], settings["resolution"], "x")
        return {"size": size, "seconds": str(settings["seconds"])}


class OpenAIModel(_SoraModel):
    PROVIDER = "openai"
