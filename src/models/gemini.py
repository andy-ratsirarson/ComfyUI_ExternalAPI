from comfy_api.latest import io

from src.models.base import Model
from src.settings.base import Resolutions, Sizes
from src.settings.video import VideoSettings, reference_image_input

STATIC_MODELS = [
    "veo-3.1-fast-generate-preview",
    "veo-3.1-fast-generate-001",
    "veo-3.1-generate-preview",
    "veo-3.1-generate-001",
    "veo-3.1-lite-generate-preview",
    "veo-2.0-generate-001",
]

RESOLUTION_MAP = {Resolutions._1K: "720p", Resolutions._2K: "1080p"}


class GeminiModel(Model):
    """Google Veo text-to-video via litellm's 'gemini/<model_id>' provider."""

    PROVIDER = "gemini"
    VIDEO_SETTINGS = VideoSettings(
        SIZE=[Sizes._16_9, Sizes._9_16],
        RESOLUTIONS=[Resolutions._1K, Resolutions._2K],
        MIN_SECONDS=4,
        MAX_SECONDS=8,
    )

    _models_cache = None

    @classmethod
    def list_models(cls) -> list[str]:
        if cls._models_cache is not None:
            return cls._models_cache

        try:
            from google import genai

            models = []
            for model in genai.Client().models.list():
                name = getattr(model, "name", "") or ""
                if name.startswith("models/"):
                    name = name[len("models/"):]
                if "veo" in name.lower():
                    models.append(name)
            cls._models_cache = models or list(STATIC_MODELS)
        except Exception:
            cls._models_cache = list(STATIC_MODELS)

        return cls._models_cache

    @staticmethod
    def _negative_prompt_input():
        return io.String.Input(
            "negative_prompt",
            default="",
            multiline=True,
            optional=True,
            tooltip="Things to avoid in the generated video.",
        )

    @classmethod
    def video_settings_inputs(cls):
        inputs = super().video_settings_inputs()
        inputs.append(
            io.Combo.Input(
                "person_generation",
                options=["allow_all", "allow_adult"],
                default="allow_all",
                tooltip="Whether people may be generated in the video.",
            )
        )
        inputs.append(cls._negative_prompt_input())
        return inputs

    @classmethod
    def image_to_video_settings_inputs(cls):
        return [
            cls.VIDEO_SETTINGS.size_input(),
            cls.VIDEO_SETTINGS.resolution_input(),
            cls.VIDEO_SETTINGS.seconds_input(),
            reference_image_input(),
            io.Combo.Input(
                "person_generation",
                options=["allow_adult"],
                default="allow_adult",
                tooltip="Whether people may be generated in the video. Image-to-video only permits allow_adult.",
            ),
            cls._negative_prompt_input(),
        ]

    @classmethod
    def video_kwargs(cls, model_id: str, settings: dict) -> dict:
        kwargs = {
            "aspectRatio": settings["size"],
            "resolution": RESOLUTION_MAP[settings["resolution"]],
            "durationSeconds": settings["seconds"],
            "personGeneration": settings["person_generation"],
        }
        if settings.get("negative_prompt"):
            kwargs["negativePrompt"] = settings["negative_prompt"]
        return kwargs

    @classmethod
    def image_to_video_kwargs(cls, model_id: str, settings: dict) -> dict:
        reference_image = settings.get("reference_image")
        if reference_image is None:
            raise ValueError("Image-to-video requires a reference_image input.")
        kwargs = cls.video_kwargs(model_id, settings)
        kwargs["input_reference"] = cls.image_tensor_to_bytesio(reference_image)
        return kwargs
