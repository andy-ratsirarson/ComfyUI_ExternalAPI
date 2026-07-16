from comfy_api.latest import io

from src.models.base import Model
from src.settings.base import Resolutions, Sizes
from src.settings.video import VideoSettings, dimensions_string


class RunwayMLModel(Model):
    PROVIDER = "runwayml"

    VIDEO_SETTINGS = VideoSettings(
        SIZE=[Sizes._16_9, Sizes._9_16],
        RESOLUTIONS=[Resolutions._1K, Resolutions._2K],
        MIN_SECONDS=5,
        MAX_SECONDS=10,
    )

    @classmethod
    def list_models(cls) -> list[str]:
        return ["gen3a_turbo", "gen4_turbo", "gen4_aleph", "gen4_image", "gen4_image_turbo"]

    @classmethod
    def video_settings_inputs(cls):
        return [
            cls.VIDEO_SETTINGS.size_input(),
            cls.VIDEO_SETTINGS.resolution_input(),
            io.Combo.Input(
                "seconds",
                options=[5, 10],
                default=5,
                tooltip="Duration in seconds — RunwayML's turbo models support 5 or 10s.",
            ),
            io.Int.Input(
                "seed",
                default=-1,
                min=-1,
                optional=True,
                tooltip="Random seed. -1 leaves it unset.",
            ),
        ]

    @classmethod
    def video_kwargs(cls, model_id: str, settings: dict) -> dict:
        ratio = dimensions_string(settings["size"], settings["resolution"], ":")
        return {
            "ratio": ratio,
            "duration": settings["seconds"],
            **({"seed": settings["seed"]} if settings.get("seed", -1) >= 0 else {}),
        }
