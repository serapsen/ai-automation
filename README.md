# Creative Automation for Scalable Social Ad Campaigns

A demo-ready local Python project that ingests campaign briefs, reuses or generates missing assets, overlays campaign messaging, and organizes outputs by product and aspect ratio. Includes an agentic monitor, diagrams, and documentation.

## Features
- **Pipeline**: Ingest brief (YAML/JSON), reuse local assets, generate missing creatives (OpenAI Image API or placeholder fallback), overlay campaign message, and save to `output/{product}/{aspect}/`.
- **Aspect Ratios**: 1:1, 9:16, 16:9.
- **Agent**: Monitors `input/briefs/`, triggers pipeline, tracks counts, flags <3 variants, drafts alert emails to console.
- **Docs**: Mermaid architecture and agentic diagrams, 1-slide roadmap, stakeholder email sample.
- **Config**: `.env` for keys, logging level, optional font path.

## Project Structure
```
creative-automation-project/
├── README.md
├── requirements.txt
├── main.py
├── .env.example
├── input/
│   ├── briefs/
│   │   └── sample_brief.yaml
│   └── assets/
├── output/
├── src/
│   ├── pipeline/
│   │   ├── asset_ingestion.py
│   │   ├── asset_generation.py
│   │   └── post_processor.py
│   └── utils/
│       └── logger.py
├── agent/
│   └── monitor.py
└── docs/
    ├── architecture_diagram.mmd
    ├── agentic_system_design.mmd
    ├── roadmap.md
    └── stakeholder_email.md
```

## Setup (Windows)
1. Install Python 3.10+.
2. Create venv and install deps:
```
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```
3. Create `.env` from `.env.example` and set `OPENAI_API_KEY` if using OpenAI image generation.

## Run the Pipeline
```
python -m main --brief input/briefs/sample_brief.yaml
```
- Outputs to `output/{product}/{aspect}/`.
- If `OPENAI_API_KEY` is not set, placeholder images are generated locally with Pillow.

## Run the Agent Monitor
- Run once:
```
python -m agent.monitor --once
```
- Watch folder (polling every 10s):
```
python -m agent.monitor --watch --interval 10
```
- Agent triggers the pipeline for each new brief and logs a draft email if assets per product/aspect are <3.

### Agent LLM Context Schema
- See `docs/mcp_context_schema.json` for the Model Context Protocol the agent would send to an LLM when drafting alerts.

## Run Tests
Use Python's builtin unittest discovery. On Windows + Git Bash, using the venv's interpreter path is most reliable:
```
./.venv/Scripts/python.exe -m unittest discover -v
```
If you prefer to activate the venv first:
```
source ./.venv/Scripts/activate
python -m unittest discover -v
```
Notes:
- Tests live under `tests/` and avoid external API calls.
- Discovery pattern defaults to files matching `test*.py`.

## Example Output
- Aspect folders on disk use `x` instead of `:` for cross-platform safety: `1x1`, `9x16`, `16x9`.
- Example after running the sample brief:
```
output/
  AlphaSneaker/
    1x1/
      gen_1.png
      gen_1_msg.png
      gen_1_final.png
    9x16/
      gen_1.png
      gen_1_msg.png
      gen_1_final.png
    16x9/
      gen_1.png
      gen_1_msg.png
      gen_1_final.png
  BetaSandal/
    1x1/ ...
    9x16/ ...
    16x9/ ...
```
- If reusing assets, expect names like `exist_1.png`, `exist_1_msg.png`, `exist_1_final.png`.
- A run summary is written to `output/summary.json` with counts and compliance per product/aspect.

## Environment
- `.env` keys:
  - `OPENAI_API_KEY` (optional)
  - `OPENAI_IMAGE_MODEL=gpt-image-1` (optional)
  - `LOG_LEVEL=INFO`
  - `FONT_PATH` (optional, path to a .ttf font)
  - `AZURE_STORAGE_CONNECTION_STRING` (preferred) or `AZURE_STORAGE_ACCOUNT`/`AZURE_STORAGE_KEY`
  - `AZURE_BLOB_CONTAINER` and optional `AZURE_BLOB_PREFIX`

### Azure example (.env)
```
LOG_LEVEL=INFO

# OpenAI (optional)
OPENAI_API_KEY=
OPENAI_IMAGE_MODEL=gpt-image-1

# Azure Blob Storage
# Preferred: single connection string
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net

# Or account + key
# AZURE_STORAGE_ACCOUNT=your_account
# AZURE_STORAGE_KEY=your_key

AZURE_BLOB_CONTAINER=ai-automation
AZURE_BLOB_PREFIX=images
```

### Storage backend selection
- Control uploads via `STORAGE_BACKEND` env (defaults to `azure`):
  - `STORAGE_BACKEND=azure` to enable Azure Blob uploads
  - `STORAGE_BACKEND=none` to disable cloud uploads

### Email (SMTP) – Office 365 / Outlook
- Minimal `.env` example:
```
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your.name@yourtenant.onmicrosoft.com
SMTP_PASS=your_app_or_smtp_password
SMTP_FROM=your.name@yourtenant.onmicrosoft.com
SMTP_STARTTLS=true

# Optional global fallback recipients; briefs can override via `notifications`.
SMTP_TO=creative.lead@yourco.com,adops@yourco.com
SMTP_CC=it@yourco.com,legal@yourco.com

# Attach run summaries (JSON/CSV) to emails
EMAIL_ATTACH_SUMMARY=true
```
- Notes:
  - Ensure the mailbox has SMTP AUTH enabled in Exchange Online.
  - `SMTP_FROM` should match the authenticated mailbox (`SMTP_USER`) unless send-as is allowed.
  - STARTTLS on port 587 is required; implicit TLS (465) is not used for Office 365.
  - If briefs define `notifications` or `notifications_by_region`, those recipients take precedence over `SMTP_TO`/`SMTP_CC`.

## Logo usage
- Set the logo file path in your brief at `brand.logo_path` (relative to repo root or absolute), e.g. `input/assets/brand/logo.png`.
- Use a transparent PNG for best results.
- The logo is auto-scaled to ~1/8 of image width and placed top-left with a margin (see `src/pipeline/post_processor.py` → `overlay_logo()`).
- If the file is missing or invalid, the pipeline completes and saves images without a logo (no error).
- To verify:
  - Run `./.venv/Scripts/python.exe -m main --brief input/briefs/sample_brief.yaml`.
  - Check `_final.png` files under `output/{product}/{aspect}/` — these include the logo overlay if present.

## OpenAI Image Models
- **Supported models for image generation**: `gpt-image-1`, `dall-e-3`.
- If an unsupported model is set (e.g., `gpt-4o`), the app logs a warning and falls back to `gpt-image-1` automatically.
- You can set the model via `.env` (`OPENAI_IMAGE_MODEL`) or per-brief (`openai_image_model`).

## Key Design Decisions
- **Local-first, cloud-ready**: Filesystem storage with optional extension to Azure Blob (easily adaptable to other clouds).
- **Model validation & fallback**: Unsupported image models automatically fall back to `gpt-image-1`.
- **Graceful resilience**: Pillow placeholder images used if API is unavailable.
- **Windows-safe paths**: Aspect directories use `1x1`, `9x16`, `16x9` on disk.
- **Accurate variant counting**: Agent counts only `*_final.png` to avoid inflated counts.
- **Compliance & moderation**: Simple brand color/logo checks and keyword moderation for demo purposes.

## Diagrams
- Mermaid files in `docs/`.
- If your IDE cannot export diagrams, open `.mmd` files in https://mermaid.live or import to draw.io/Excalidraw to export PNG/SVG.

## Example Brief
See `input/briefs/sample_brief.yaml`.

## Limitations
- OpenAI image generation requires an API key and may incur costs.
- Non-square images are derived by resizing/cropping from a base image.
- Brand compliance checks are simplified (color usage and optional logo overlay).
- Text moderation is a simple keyword blocker for demo purposes.

## Troubleshooting
- **No images generated**: Ensure `OPENAI_API_KEY` is set or expect Pillow placeholders.
- **Logo not applied**: Verify `brand.logo_path` exists (e.g., `input/assets/brand/logo.png`).
- **Fonts look off**: Set `FONT_PATH` to a valid `.ttf`.
- **Model errors**: If using unsupported models (e.g., `gpt-4o` for Images API), the app falls back to `gpt-image-1` and logs a warning.

## Demo Recording Checklist
- **Prepare**: Ensure `.venv` is created, deps installed, and `.env` configured (Azure/OpenAI as desired).
- **Show brief**: Open `input/briefs/sample_brief.yaml` (products, region, audience, message).
- **Run pipeline**: `python -m main --brief input/briefs/sample_brief.yaml` from repo root.
- **Outputs**: Show `output/{product}/{aspect}/*_final.png` and `output/summary.json`.
- **Optional uploads**: Show Azure Blob container with uploaded files if configured.
- **Agent**: Optionally run `python -m agent.monitor --once` and show logs.

## License
MIT (for take-home demo purposes).
