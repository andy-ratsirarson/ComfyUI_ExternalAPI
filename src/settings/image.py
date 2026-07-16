from comfy_api.latest import io

from src.settings.base import Resolutions, Settings, Sizes

IMAGE_SIZES = [
    Sizes._21_9,
    Sizes._16_9,
    Sizes._3_2,
    Sizes._4_3,
    Sizes._5_4,
    Sizes._1_1,
    Sizes._4_5,
    Sizes._3_4,
    Sizes._2_3,
    Sizes._9_16,
]
IMAGE_RESOLUTIONS = [Resolutions._480, Resolutions._720, Resolutions._1080, Resolutions._4K]

DEFAULT_MIN_IMAGES = 1


class ImageSettings(Settings):
    """A model's image generation bounds: which of the master SIZE/RESOLUTIONS
    options it supports, and how many images it can generate per call."""

    MIN_IMAGES: int = DEFAULT_MIN_IMAGES
    MAX_IMAGES: int

    def num_images_input(self, default=None):
        return io.Int.Input(
            "num_images",
            default=default if default is not None else self.MIN_IMAGES,
            min=self.MIN_IMAGES,
            max=self.MAX_IMAGES,
            tooltip=f"Number of images to generate at once ({self.MIN_IMAGES}-{self.MAX_IMAGES}).",
        )
