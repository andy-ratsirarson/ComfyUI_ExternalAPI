from enum import Enum

from comfy_api.latest import io
from pydantic import BaseModel


class Sizes(str, Enum):
    """Every aspect ratio used anywhere in the app. Add a new ratio here once;
    every model's SIZE list references these members instead of a raw string."""

    _21_9 = "21:9"
    _16_9 = "16:9"
    _4_3 = "4:3"
    _1_1 = "1:1"
    _3_4 = "3:4"
    _9_16 = "9:16"
    _3_2 = "3:2"
    _5_4 = "5:4"
    _4_5 = "4:5"
    _2_3 = "2:3"


class Resolutions(str, Enum):
    """Every resolution tier used anywhere in the app. Add a new tier here
    once; every model's RESOLUTIONS list references these members instead of
    a raw string."""

    _480 = "480"
    _720 = "720"
    _1080 = "1080"
    _1K = "1K"
    _2K = "2K"
    _4K = "4K"


class Settings(BaseModel):
    """Base config for a modality (image/video): the generic size/resolution
    options a model supports, plus the io.Input builders shared by both."""

    SIZE: list[Sizes]
    RESOLUTIONS: list[Resolutions]

    def size_input(self, default=None):
        return io.Combo.Input(
            "size",
            options=list(self.SIZE),
            default=default if default is not None else self.SIZE[0],
            tooltip="Aspect ratio of the generated output.",
        )

    def resolution_input(self, default=None):
        return io.Combo.Input(
            "resolution",
            options=list(self.RESOLUTIONS),
            default=default if default is not None else self.RESOLUTIONS[0],
            tooltip="Output resolution tier.",
        )
