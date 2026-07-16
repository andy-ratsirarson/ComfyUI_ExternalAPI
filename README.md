# ComfyUI_ExternalAPI

BYOK (bring-your-own-key) ComfyUI nodes for generating video through external providers — Gemini/Veo, OpenAI Sora, Azure, and RunwayML — via [LiteLLM](https://github.com/BerriAI/litellm). No local GPU-hungry model required; you supply your own provider API key and pay that provider directly.

> **Status:** text-to-video works for all providers; image-to-video (a reference image guiding the animation) works for Gemini/Veo only. Text-to-image is planned as a separate node — see [Roadmap](#roadmap).

## Features

- **One node, every provider.** Pick a provider from a dropdown; the node's fields update to show only that provider's real parameters.
- **BYOK.** Your API key never touches this repo or any third party beyond the provider itself. Prefer setting it as a server-side environment variable; an optional in-node override exists for convenience (see [Security note](#security-note)).
- **Provider-accurate parameters.** Each provider exposes its own supported aspect ratios, resolution tiers, and duration range — no guessing which combination is valid.

## Supported providers & models

| Provider | `provider` value | Models | Aspect ratios | Resolutions | Duration |
|---|---|---|---|---|---|
| Google Gemini (Veo) | `gemini` | Fetched live from your account via `google-genai`; falls back to a built-in list (`veo-3.1-fast-generate-preview`, `veo-3.1-fast-generate-001`, `veo-3.1-generate-preview`, `veo-3.1-generate-001`, `veo-3.1-lite-generate-preview`, `veo-2.0-generate-001`) if that fails | 16:9, 9:16 | 1K, 2K | 4–8s |
| OpenAI (Sora) | `openai` | `sora-2`, `sora-2-pro`, `sora-2-pro-high-res` | 16:9, 9:16 | 1K, 2K | 4–12s* |
| Azure OpenAI (Sora) | `azure` | `sora-2`, `sora-2-pro`, `sora-2-pro-high-res` | 16:9, 9:16 | 1K, 2K | 4–12s* |
| RunwayML | `runwayml` | `gen3a_turbo`, `gen4_turbo`, `gen4_aleph`, `gen4_image`, `gen4_image_turbo` | 16:9, 9:16 | 1K, 2K | 5s or 10s |

\* OpenAI/Azure's upper duration bound isn't published by the provider; 12s is a conservative default rather than a confirmed hard limit.

Gemini's model list is fetched live from `google.genai.Client().models.list()` at node-registration time when a Gemini API key is available on the ComfyUI server, so new Veo releases show up automatically without an update to this package.

**Image-to-video** (a reference image conditioning the result) is currently supported for **Gemini/Veo only**. The other providers are text-to-video only for now — see [Roadmap](#roadmap). The models, aspect ratios, resolutions, and durations in the table above apply to both text- and image-to-video.

## Requirements

- ComfyUI with the V3 node API (`comfy_api.latest`).
- Python dependencies (installed automatically, see `requirements.txt`):
  - `litellm==1.92.0`
  - `google-genai==1.47.0`
- An API key from at least one of the providers above.

## Installation

**Via ComfyUI Manager:** search for `ComfyUI_ExternalAPI` and install.

**Manually:**

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/andy-ratsirarson/ComfyUI_ExternalAPI.git
cd ComfyUI_ExternalAPI
pip install -r requirements.txt
```

Restart ComfyUI afterward.

## Setup: API keys

Set the environment variable(s) for whichever provider(s) you plan to use **on the machine running the ComfyUI server**, then restart ComfyUI.

| Provider | Environment variable(s) |
|---|---|
| Gemini | `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) |
| OpenAI | `OPENAI_API_KEY` |
| Azure OpenAI | `AZURE_API_KEY`, `AZURE_API_BASE` (your endpoint), `AZURE_API_VERSION` (optional) |
| RunwayML | `RUNWAYML_API_SECRET` (or `RUNWAYML_API_KEY`) |

### Security note

The node also has an optional `api_key` input that overrides the environment variable for that run. **Prefer the environment variable.** Anything typed into `api_key` gets saved into the workflow JSON and into output file metadata — so it can leak if you share a workflow or an output file. Only use it for quick one-off testing.

## Usage

1. Add the node: right-click canvas → Add Node → `external_api/video` → **API Video Generate (BYOK)**.
2. Enter a text `prompt`.
3. Under `source`, leave it on `text` for text-to-video (see [Image-to-video](#image-to-video-geminiveo) below for the `image` option).
4. Pick a `provider` — the node reveals that provider's `model` dropdown.
5. Pick a `model` — the node reveals that model's settings: `size` (aspect ratio), `resolution`, `seconds` (duration), and any provider-specific extras (e.g. Gemini's `person_generation`/`negative_prompt`, RunwayML's `seed`).
6. Run the graph. The node polls the provider until the video finishes, then outputs a `VIDEO`.

Optional inputs: `api_key` (see [Security note](#security-note)), `poll_interval` (seconds between status checks, default 10), `timeout` (max seconds to wait, default 600).

### Image-to-video (Gemini/Veo)

To animate a reference image instead of generating from text alone:

1. Set `source` to `image`. The node reveals a `provider` dropdown that currently lists only `gemini`.
2. Pick `gemini`, then pick a Veo `model` — same models as text-to-video.
3. The node reveals: `size` (aspect ratio: 16:9 or 9:16), `resolution` (1K/2K), `seconds` (4–8s), `reference_image`, `person_generation`, and an optional `negative_prompt`.
4. Set `reference_image`. This is a file picker + upload widget that works exactly like ComfyUI's built-in **Load Image** node: choose an image already in ComfyUI's input folder from the dropdown, or click upload to add a new one. You can also drag an image straight from the results gallery onto the widget — ComfyUI copies it into the input folder and selects it. (It's a widget on the node, not a socket you wire from another node's output.)
5. Enter a `prompt`. It's still required with image-to-video — the prompt directs how the reference image is animated.
6. Run the graph. As with text-to-video, the node polls until the video finishes and outputs a `VIDEO`.

**Note:** for image-to-video, `person_generation` only offers `allow_adult` (text-to-video also offers `allow_all`). Google restricts generation to adults when a reference photo is provided, so the broader option isn't available here.

This currently supports exactly **one** reference image per generation. It does not (yet) support multiple reference images, tagging/naming images for reference within the prompt text, or interpolation/video-extension — see [Roadmap](#roadmap).

## Roadmap

- **Image generation** — a separate `APIImageGenerate` node, tracked in [issue #2](https://github.com/andy-ratsirarson/ComfyUI_ExternalAPI/issues/2).
- **Image-to-video** — implemented for Gemini/Veo (set `source` to `image`), single reference image only. Support for the other providers (OpenAI/Azure Sora, RunwayML) is future work.
- **Multi-image references** — RunwayML supports referencing several images at once (with in-prompt tagging), and Gemini/Veo 3.1 separately supports up to 3 reference images plus last-frame interpolation and video extension. None of this richer, multi-image capability is implemented yet — today's image-to-video is single-image only for both providers that support it at all.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests fake just enough of `comfy_api.latest` (see `tests/conftest.py`) to exercise the nodes outside a real ComfyUI install — no GPU or ComfyUI checkout required.

## License

MIT — see [LICENSE](LICENSE).
