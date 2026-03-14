# Project Overview

## Project Name
AI-Driven 2D to 3D Jewelry Generation with Real-Time Customization (PS-01)

## Mission
Build a modular AI + CAD system that converts jewelry design inputs into editable 3D assets and enables fast, component-level customization without full regeneration.

## Problem Summary
Existing workflows can generate attractive 2D jewelry concepts, but converting those concepts into production-useful 3D models and supporting fast customization remains difficult.

The project solves two linked problems:
- Reliable conversion from design input to structured 3D jewelry output.
- Real-time editing of gemstones, materials, and selected dimensions without re-running full generation pipelines.

## Target Users
- Jewelry designers who need fast concept-to-3D iteration.
- Retail/visualization teams that need interactive product previews.

## Product Goals
- Accept jewelry design intent from user inputs.
- Produce high-quality initial outputs with realistic default materials/gemstones.
- Maintain a component-aware editable structure.
- Support low-latency customization updates.
- Provide manufacturability signals and cost estimation.
- Export manufacturing-usable files.

## Confirmed MVP Scope (Locked)
- Jewelry type: Rings only.
- Primary implementation path: Prompt-first deterministic interpretation -> parametric template initialization -> structured 3D model.
- Sketch upload path: Experimental seed path for secondary iteration and future fidelity track.
- Runtime mode: Single-user local session.
- Primary outputs: GLB for web visualization and STL for manufacturing export.
- Interactive latency target: 200 ms to 1 s for selected edits.
- MVP edit operations required in latency target:
  - Material swaps.
  - Gemstone type swaps.
  - Gemstone size changes.
  - Band thickness changes.

## Must-Have Functional Features
1. Input to concept generation
- Inputs discussed: text prompt, rough sketch, reference image.
- MVP priority path is text prompt first, interpreted into template-aware ring parameters.
- Output: polished, editable ring initialized from template/style defaults.

2. 2D to 3D generation
- Generate structured 3D model suitable for rendering and export.
- Geometry must be clean and watertight for downstream use.

3. Component-aware structure
- Recognize and model ring subcomponents (band, center stone, side stones, prongs/settings).
- Preserve semantic structure so edits target components instead of whole-mesh regeneration.

4. Real-time customization
- Edit materials, gemstone choices, and key dimensions.
- Update model quickly via parametric graph changes.

5. Realistic rendering
- Interactive PBR rendering in web viewer.
- High-quality photoreal renders via offline render pipeline.

6. Cost estimation
- Estimate cost from metal weight, gemstone type/size, and rule-based logic.

## High-Impact Extras (Planned Beyond Core MVP)
- Design variations generator (Generate 5 variants).
- Style transfer presets (minimalist, vintage, royal, art deco, luxury).
- Catalog image generation (studio/background variants, 360 assets).
- AR try-on (roadmap only for now).
- Expanded manufacturability checks.
- Additional CAD export paths (for example STEP in later phase).

## Demo Priorities
- Highest priority: Fast interactive customization + stability.
- Visual quality should be strong, but no live dependency on heavy GPU inference in demo mode.

## Operational Context
- Development machine may use RTX 4070 for precompute.
- Demo environment expected on laptops without discrete GPU.
- Live demo loop must remain CPU-safe by avoiding heavy on-demand inference.
