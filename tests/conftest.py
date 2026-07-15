"""Stubs the parts of `comfy_api.latest` our nodes touch.

`comfy_api` only exists inside a running ComfyUI install, so unit tests fake
just enough of its surface (io.Schema/Input/Output/NodeOutput, ComfyAPI,
InputImpl.VideoFromFile) to import and exercise src/nodes.py in isolation.
"""

import sys
import types


def _install_fake_comfy_api():
    if "comfy_api.latest" in sys.modules:
        return

    class _InputSpec:
        def __init__(self, name, **kwargs):
            self.name = name
            self.kwargs = kwargs

    class _InputFactory:
        @staticmethod
        def Input(name, **kwargs):
            return _InputSpec(name, **kwargs)

    class _OutputSpec:
        def __init__(self, name=None, **kwargs):
            self.name = name
            self.kwargs = kwargs

    class _OutputFactory:
        @staticmethod
        def Output(name=None, **kwargs):
            return _OutputSpec(name, **kwargs)

    class String(_InputFactory):
        pass

    class Float(_InputFactory):
        pass

    class Video(_OutputFactory):
        pass

    class Hidden:
        unique_id = "unique_id"

    class Schema:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class NodeOutput:
        def __init__(self, *args):
            self.args = args

    class ComfyNode:
        hidden = None

    io = types.SimpleNamespace(
        String=String,
        Float=Float,
        Video=Video,
        Hidden=Hidden,
        Schema=Schema,
        NodeOutput=NodeOutput,
        ComfyNode=ComfyNode,
    )

    class ComfyExtension:
        async def get_node_list(self):
            raise NotImplementedError

    class _Execution:
        async def set_progress(self, value, max_value, node_id=None, **kwargs):
            return None

    class ComfyAPI:
        def __init__(self):
            self.execution = _Execution()

    class VideoFromFile:
        def __init__(self, file_obj):
            self.file_obj = file_obj

    InputImpl = types.SimpleNamespace(VideoFromFile=VideoFromFile)

    latest = types.SimpleNamespace(
        io=io,
        ComfyExtension=ComfyExtension,
        ComfyAPI=ComfyAPI,
        InputImpl=InputImpl,
    )

    comfy_api = types.ModuleType("comfy_api")
    comfy_api.latest = latest

    sys.modules["comfy_api"] = comfy_api
    sys.modules["comfy_api.latest"] = latest


_install_fake_comfy_api()
