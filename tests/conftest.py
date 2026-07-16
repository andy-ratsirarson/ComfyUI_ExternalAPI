"""Stubs the parts of `comfy_api.latest` (and `folder_paths`) our nodes touch.

Both only exist inside a running ComfyUI install, so unit tests fake just
enough of their surface (io.Schema/Input/Output/NodeOutput, ComfyAPI,
InputImpl.VideoFromFile, folder_paths' input-directory helpers) to import and
exercise src/nodes.py in isolation.
"""

import os
import sys
import tempfile
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

    class Int(_InputFactory):
        pass

    class Combo(_InputFactory):
        pass

    class _DynamicComboOption:
        def __init__(self, key, inputs):
            self.key = key
            self.inputs = inputs

    class _DynamicComboInputSpec(_InputSpec):
        def __init__(self, name, options=None, **kwargs):
            super().__init__(name, options=options, **kwargs)
            self.options = options or []

    class DynamicCombo:
        Option = _DynamicComboOption

        @staticmethod
        def Input(id, options=None, **kwargs):
            return _DynamicComboInputSpec(id, options=options, **kwargs)

    class Video(_OutputFactory):
        pass

    class UploadType:
        image = "image_upload"
        audio = "audio_upload"
        video = "video_upload"
        model = "file_upload"

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
        Int=Int,
        Combo=Combo,
        DynamicCombo=DynamicCombo,
        Video=Video,
        UploadType=UploadType,
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


def _install_fake_folder_paths():
    if "folder_paths" in sys.modules:
        return

    fake_input_dir = tempfile.mkdtemp(prefix="fake_comfy_input_")

    def get_input_directory():
        return fake_input_dir

    def filter_files_content_types(files, content_types):
        return files

    def get_annotated_filepath(name, default_dir=None):
        return os.path.join(default_dir or fake_input_dir, name)

    def exists_annotated_filepath(name):
        return os.path.isfile(os.path.join(fake_input_dir, name))

    fake_module = types.ModuleType("folder_paths")
    fake_module.get_input_directory = get_input_directory
    fake_module.filter_files_content_types = filter_files_content_types
    fake_module.get_annotated_filepath = get_annotated_filepath
    fake_module.exists_annotated_filepath = exists_annotated_filepath
    sys.modules["folder_paths"] = fake_module


_install_fake_comfy_api()
_install_fake_folder_paths()
