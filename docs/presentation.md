# Creative Automation for Scalable Social Ad Campaigns – POC Deck

## Agenda
- **Problem & Objectives**
- **Task 1:** Architecture & Roadmap
- **Task 2:** Pipeline POC (Demo)
- **Task 3:** Agentic System & Comms
- **Design Decisions, Limitations, Next Steps**

## Problem & Objectives
- **Accelerate velocity** of localized campaign production.
- **Ensure brand consistency** across markets and languages.
- **Maximize relevance** via personalization.
- **Optimize ROI** through efficiency and performance.
- **Enable insights** via structured outputs and logs.

## Task 1 – Architecture & Roadmap
- **Architecture**: [architecture_diagram.mmd](architecture_diagram.mmd) – refined with layers and modern AI models
- **Data Flow**: [data_flow_diagram.mmd](data_flow_diagram.mmd) – transformations and metadata tracking
- **Storage**: Local `input/assets/` with optional Azure Blob uploads
- **GenAI**: DALL·E 3 (Azure OpenAI or OpenAI.com) with Pillow fallback for resilience
- **Localization**: English plus optional languages per brief; optional translation via Azure/OpenAI Chat; per-language outputs with `_*_{lang}_final.png`
- **Outputs**: Structured `output/{product}/{aspect}/` with naming conventions
- **Compliance**: Automated brand color and logo presence checks

### Roadmap (1 Slide)
- See [roadmap.md](roadmap.md) for detailed timeline.
- Epics: Architecture (1d), Pipeline (3d), Agent & Reporting (2d).
- Roles: Creative Lead, AdOps, IT, Legal/Compliance.

## Task 2 – Pipeline POC
- Entrypoint: [`main.py`](../main.py) → `run_pipeline()`.
- Modules:
  - [`src/pipeline/asset_ingestion.py`](../src/pipeline/asset_ingestion.py): load brief, discover assets, normalize aspects.
  - [`src/pipeline/asset_generation.py`](../src/pipeline/asset_generation.py): per-language image gen via DALL·E 3 (Azure/OpenAI) or placeholder; aspect resize; meta sidecar with source.
  - [`src/pipeline/post_processor.py`](../src/pipeline/post_processor.py): text overlay (placeholders and reused assets only), logo overlay, moderation, compliance summary.
  - [`src/utils/logger.py`](../src/utils/logger.py): configurable logging.
- Aspect ratios: `1:1`, `9:16`, `16:9`.
- Reuse existing assets if present, otherwise generate.
- Message overlay and optional logo overlay.

### Demo Steps (Local)
1. Create venv and install dependencies (Windows):
   ```
   py -3 -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure environment:
   - Copy [`.env.example`](../.env.example) (or `ENV.EXAMPLE.txt`) to `.env`.
   - If you don't want cloud uploads in the demo:
     ```
     STORAGE_BACKEND=none
     ```
   - Optional GenAI (for real image generation; else Pillow placeholders):
    ```
    # Option A: Azure OpenAI (preferred when available)
    AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
    AZURE_OPENAI_API_KEY=...
    AZURE_OPENAI_DEPLOYMENT=dall-e-3
    OPENAI_API_VERSION=2024-04-01-preview

    # Option B: OpenAI.com
    OPENAI_API_KEY=...
    OPENAI_IMAGE_MODEL=dall-e-3
    ```
  - Optional Localization:
    ```
    # Brief example
    languages: ["en", "tr"]  # English always included

    # Translation providers (optional)
    AZURE_OPENAI_TRANSLATE_DEPLOYMENT=gpt-4o-mini  # Azure Chat
    OPENAI_TRANSLATE_MODEL=gpt-4o-mini             # OpenAI.com fallback
    ```
   - Optional SMTP email (SendGrid implicit TLS 465 example):
     ```
     SMTP_HOST=smtp.sendgrid.net
     SMTP_PORT=465
     SMTP_SSL=true
     SMTP_STARTTLS=false
     SMTP_USER=apikey
     SMTP_PASS=YOUR_SENDGRID_API_KEY
     SMTP_FROM=verified@yourdomain.com
     SMTP_TO=you@yourdomain.com
     ```

3. Run the pipeline for the sample brief:
   ```
   python -m main --brief input/briefs/sample_brief.yaml
   ```
   - See [sample_brief.yaml](../input/briefs/sample_brief.yaml) for structure.

4. Optional: Run a second brief to show APAC variant:
   ```
   python -m main --brief input/briefs/sample_brief_apac.yaml
   ```

5. Run the Agent Monitor (alerts and email):
   ```
   python -m agent.monitor --once --force
   ```
    - Counts variants per product/aspect and either sends SMTP email (if configured) or logs a draft to console.
    - With localization enabled, files are suffixed by language (e.g., `_en_final.png`, `_tr_final.png`). AI images keep logo only; placeholders and reused assets include a bottom message bar per language.

## Task 3 – Agentic System & Comms
- **System Design**: [agentic_system_design.mmd](agentic_system_design.mmd) – enhanced with detailed orchestration flow
- **Agent Monitor**: [`agent/monitor.py`](../agent/monitor.py) with intelligent polling and state management
- **Variant Tracking**: Automated counting with configurable thresholds (default: 3)
- **Alert System**: SMTP email (if configured) or console draft; recipient routing (Creative Lead, AdOps, IT, Legal)
- **MCP Context Schema**: [mcp_context_schema.json](mcp_context_schema.json) – defines LLM-visible data structure
- **Sample Communication**: [stakeholder_email.md](stakeholder_email.md) – demonstrates professional escalation

## Design Decisions
- **Local-first** with cloud-ready boundaries (assets, GenAI, outputs).
- **Graceful fallback** when API key missing or rate-limited.
- **Simple compliance & moderation** for demo; extensible rules engine possible.
- **Clean package layout** for readability and modularity.

## Assumptions
- Images can be resized/cropped to meet aspect targets.
- One variant per missing asset satisfies POC; target counts enforced via agent alerts.
- English copy acceptable for demo; i18n can be added later.

## Limitations
- Placeholder images lack photorealism; relies on external GenAI for quality.
- No persistence layer beyond filesystem.
- SMTP email is supported when configured; no BI integration.

## Next Steps
 - Enhance Azure Blob integration for `assets_root` and outputs.
- Harden SMTP deliverability (domain auth, suppression management), multi-provider presets (SendGrid/Office365), and monitoring.
- Scalable variant generation loop and A/B tracking metadata.
- Compliance DSL (brand palettes, logo placement rules, legal strings).
