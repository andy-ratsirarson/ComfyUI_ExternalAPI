from comfy_api.latest import io


class Model:
    """Base class for all provider/model integrations.

    Subclasses set PROVIDER and VIDEO_SETTINGS (a settings.video.VideoSettings
    instance declaring which SIZE/RESOLUTIONS subset and duration range this
    provider supports), and implement list_models() + video_kwargs().
    """

    PROVIDER: str = None
    VIDEO_SETTINGS = None

    @classmethod
    def list_models(cls) -> list[str]:
        """Return this provider's available model ids for text-to-video."""
        raise NotImplementedError(f"list_models not implemented for {cls.__name__}.")

    @classmethod
    def video_settings_inputs(cls):
        """Build the io.Input list revealed once a specific model is selected."""
        if cls.VIDEO_SETTINGS is None:
            raise NotImplementedError(f"{cls.__name__} does not support video generation.")
        return [
            cls.VIDEO_SETTINGS.size_input(),
            cls.VIDEO_SETTINGS.resolution_input(),
            cls.VIDEO_SETTINGS.seconds_input(),
        ]

    @classmethod
    def video_kwargs(cls, model_id: str, settings: dict) -> dict:
        """Translate the generic {size, resolution, seconds, ...} dict captured by
        the node's DynamicCombo into the litellm avideo_generation kwargs this
        provider's API expects (e.g. Gemini's aspectRatio/resolution/durationSeconds)."""
        raise NotImplementedError(f"video_kwargs not implemented for {cls.__name__}.")

    @classmethod
    def image_to_video_settings_inputs(cls):
        """Build the io.Input list revealed once a specific model is selected,
        for the image-to-video ('image' source) path. Distinct from
        video_settings_inputs() because providers can genuinely differ here
        (e.g. Gemini restricts person_generation to fewer options)."""
        raise NotImplementedError(f"{cls.__name__} does not support image-to-video.")

    @classmethod
    def image_to_video_kwargs(cls, model_id: str, settings: dict) -> dict:
        """Translate the generic settings dict (including the resolved reference
        image path) into the litellm avideo_generation kwargs this provider's
        API expects for image-to-video."""
        raise NotImplementedError(f"image_to_video_kwargs not implemented for {cls.__name__}.")

    @classmethod
    def model_combo_option(cls, mode="text"):
        """Build this provider's DynamicCombo.Option: a nested 'model' combo where
        each model reveals this provider's settings for the given source mode
        ("text" = text-to-video, "image" = image-to-video)."""
        build_inputs = cls.video_settings_inputs if mode == "text" else cls.image_to_video_settings_inputs
        return io.DynamicCombo.Option(
            cls.PROVIDER,
            [
                io.DynamicCombo.Input(
                    "model",
                    options=[
                        io.DynamicCombo.Option(model_id, build_inputs())
                        for model_id in cls.list_models()
                    ],
                ),
            ],
        )

    def image_to_image(self, *args, **kwargs):
        raise NotImplementedError("image_to_image not implemented for this model.")

    def text_to_image(self, *args, **kwargs):
        raise NotImplementedError("text_to_image not implemented for this model.")

    def text_to_video(self, *args, **kwargs):
        raise NotImplementedError("text_to_video not implemented for this model.")

    def text_to_text(self, *args, **kwargs):
        raise NotImplementedError("text_to_text not implemented for this model.")