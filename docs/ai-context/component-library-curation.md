# Component Library Curation Guide

## Goal
Build a demo-ready ring component pack that replaces procedural fallback meshes with curated reusable assets while preserving low-latency parameter edits.

## Recommended Source Strategy
1. Primary source pool: jewelry-tagged CAD models from community repositories with explicit license records.
2. Secondary source pool: internal handcrafted assets exported to GLB for immediate demo safety.
3. Keep all sources in a manifest with per-component provenance and rights metadata.

## MVP Curation Targets
- Band components: 4
- Setting components: 4
- Style components: 4
- Accent components: 4
- Optional gemstone variants: 3

Target total for first strong showcase: 16 to 24 curated parts.

## Mandatory Metadata Per Component
- id
- target_component_id
- source_url
- source_name
- license
- status (approved/candidate/disabled)
- file path
- fit calibration values
- tags and quality_score

## Quality Gates
1. License gate
- Reject components with unknown or incompatible rights for demo use.

2. Geometry gate
- Mesh loads without scene/geometry errors.
- No critical non-manifold breakage for intended stage.
- Reasonable triangle budget for interactive viewer.

3. Fit gate
- Component aligns with ring assembly anchor assumptions.
- Scale responds correctly to gemstone size, setting height, and band size.

4. Visual gate
- Side-by-side review against procedural fallback.
- Must improve silhouette and close-up readability.

## Workflow
1. Add candidate entries in apps/backend/assets/components/manifest.json.
2. Place files under apps/backend/assets/components/<category>/.
3. Run audit script:
   - uv run python scripts/component_catalog_audit.py
4. Promote candidate -> approved only after license + geometry + fit checks.
5. Re-run backend tests.

## Rollout Plan
1. Hero solitaire pack first:
- band.classic
- band.tapered
- setting.solitaire
- setting.royal_crown
- style.cathedral_arms
- accent.solitaire_shoulders

2. Halo and pave pack second.

3. Vintage and split-shank pack third.

## Notes
- Current backend assembly automatically uses approved file-backed overrides when available and falls back to procedural components otherwise.
- This ensures demo stability even while curation is in progress.
