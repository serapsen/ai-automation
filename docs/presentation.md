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
- **Storage**: Local `input/assets/` (extensible to Dropbox/Azure/AWS)
- **GenAI**: OpenAI DALL-E 3 API with Pillow fallback for resilience
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
  - [`src/pipeline/asset_generation.py`](../src/pipeline/asset_generation.py): OpenAI image gen (if key) or Pillow placeholder; aspect resize.
  - [`src/pipeline/post_processor.py`](../src/pipeline/post_processor.py): text overlay, logo overlay, moderation, compliance summary.
  - [`src/utils/logger.py`](../src/utils/logger.py): configurable logging.
- Aspect ratios: `1:1`, `9:16`, `16:9`.
- Reuse existing assets if present, otherwise generate.
- Message overlay and optional logo overlay.

### Demo Steps (Local)
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: Copy [`.env.example`](../.env.example) to `.env` and set `OPENAI_API_KEY` (optional).
3. Run pipeline: `python -m main --brief input/briefs/sample_brief.yaml`
   - See [sample_brief.yaml](../input/briefs/sample_brief.yaml) for structure.
4. Inspect outputs in `output/AlphaSneaker/*` and `output/BetaSandal/*`.

## Task 3 – Agentic System & Comms
- **System Design**: [agentic_system_design.mmd](agentic_system_design.mmd) – enhanced with detailed orchestration flow
- **Agent Monitor**: [`agent/monitor.py`](../agent/monitor.py) with intelligent polling and state management
- **Variant Tracking**: Automated counting with configurable thresholds (default: 3)
- **Alert System**: Stakeholder email drafts with recipient routing (Creative Lead, AdOps, IT, Legal)
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
- No real email or BI integration (console logs for demo).

## Next Steps
- Add Dropbox/Azure blob integration for `assets_root` and outputs.
- Email integration (SMTP/Outlook) and notifications.
- Scalable variant generation loop and A/B tracking metadata.
- Compliance DSL (brand palettes, logo placement rules, legal strings).
