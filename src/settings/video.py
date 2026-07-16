import os

import folder_paths
from comfy_api.latest import io

from src.settings.base import Resolutions, Settings, Sizes

VIDEO_SIZES = [Sizes._21_9, Sizes._16_9, Sizes._4_3, Sizes._1_1, Sizes._3_4, Sizes._9_16]
VIDEO_RESOLUTIONS = [Resolutions._1K, Resolutions._2K, Resolutions._4K]

DEFAULT_MIN_SECONDS = 5

# Canonical (size, resolution) -> (width, height) pixel dimensions. Providers
# that take a single literal dimension string (e.g. Sora's "1280x720", Runway's
# "1280:720") format from this instead of keeping their own duplicate table.
DIMENSIONS = {
    (Sizes._16_9, Resolutions._1K): (1280, 720),
    (Sizes._16_9, Resolutions._2K): (1920, 1080),
    (Sizes._9_16, Resolutions._1K): (720, 1280),
    (Sizes._9_16, Resolutions._2K): (1080, 1920),
}


def dimensions_string(size: str, resolution: str, separator: str) -> str:
    """Format the canonical pixel dimensions for (size, resolution) using the
    given separator, e.g. dimensions_string("9:16", "2K", ":") -> "1080:1920"."""
    width, height = DIMENSIONS[(size, resolution)]
    return f"{width}{separator}{height}"


def reference_image_input(id="reference_image", optional=True):
    """A file-picker + upload widget for image-to-video, matching ComfyUI's
    built-in LoadImage/LoadVideo convention: lists existing files already in
    the input directory and lets the user upload a new one. Yields a filename;
    resolve it to a real path with folder_paths.get_annotated_filepath()."""
    input_dir = folder_paths.get_input_directory()
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    files = folder_paths.filter_files_content_types(files, ["image"])
    return io.Combo.Input(
        id,
        options=sorted(files),
        upload=io.UploadType.image,
        optional=optional,
        tooltip="Reference image to seed the video. Pick an existing upload or click to upload a new one.",
    )


class VideoSettings(Settings):
    """A model's video generation bounds: which of the master SIZE/RESOLUTIONS
    options it supports, and its supported duration range."""

    MIN_SECONDS: int = DEFAULT_MIN_SECONDS
    MAX_SECONDS: int

    def seconds_input(self, default=None, step=1):
        return io.Int.Input(
            "seconds",
            default=default if default is not None else self.MIN_SECONDS,
            min=self.MIN_SECONDS,
            max=self.MAX_SECONDS,
            step=step,
            tooltip=f"Video duration in seconds ({self.MIN_SECONDS}-{self.MAX_SECONDS}s for this model).",
        )
