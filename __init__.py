from typing_extensions import override

from comfy_api.latest import ComfyExtension, io

from .src.nodes import NODES


class ExternalApiExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return NODES


async def comfy_entrypoint() -> ExternalApiExtension:
    return ExternalApiExtension()
