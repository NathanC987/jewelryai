"use client";

import { useEffect, useState } from "react";

import { RingWorkbench } from "../components/ring-workbench";
import { ViewerCanvas } from "../components/viewer-canvas";

type SketchUploadResponse = {
  sketch_id: string;
  extracted_parameters: {
    template_id: "solitaire_ring" | "halo_ring" | "pave_band_ring" | "split_shank_ring" | "three_stone_ring";
    style_tag: "modern" | "vintage" | "royal" | "minimalist";
    metal: "gold" | "rose_gold" | "platinum" | "silver";
    gemstone_type: "diamond" | "ruby" | "emerald" | "sapphire";
    center_stone_shape: "round" | "oval" | "princess" | "emerald_cut" | "marquise" | "pear";
    prong_count: number;
    band_profile: "classic" | "flat" | "knife_edge" | "tapered";
    side_stone_count: number;
    setting_family: "basket" | "peghead" | "bezel" | "halo" | "cluster";
    setting_variant: number;
    setting_openheart: boolean;
    shank_family: "classic" | "cathedral" | "advanced";
    shank_variant: number;
    setting_height_mm: number;
    gemstone_size_mm: number;
    band_thickness_mm: number;
  };
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export default function HomePage() {
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);
  const [isRightPanelCollapsed, setIsRightPanelCollapsed] = useState(false);
  const [sketchFileName, setSketchFileName] = useState<string | null>(null);
  const [sketchPreviewUrl, setSketchPreviewUrl] = useState<string | null>(null);
  const [sketchParameters, setSketchParameters] = useState<SketchUploadResponse["extracted_parameters"] | null>(null);
  const [isSketchUploading, setIsSketchUploading] = useState(false);
  const [sketchUploadError, setSketchUploadError] = useState<string | null>(null);
  const [ringParameters, setRingParameters] = useState<{
    metal: "gold" | "rose_gold" | "platinum" | "silver";
    gemstone_type: "diamond" | "ruby" | "emerald" | "sapphire";
  } | null>(null);
  const [ringSummary, setRingSummary] = useState<{
    estimatedPriceUsd: number;
    pricingSource: "live" | "cached" | "baseline";
    ratesTimestampUtc: string | null;
    ratesAgeSeconds: number | null;
    manufacturabilityWarnings: { code: string; message: string }[];
  } | null>(null);

  useEffect(() => {
    return () => {
      if (sketchPreviewUrl) {
        URL.revokeObjectURL(sketchPreviewUrl);
      }
    };
  }, [sketchPreviewUrl]);

  function triggerPromptGeneration() {
    window.dispatchEvent(
      new CustomEvent("ring-generate-from-prompt", {
        detail: {
          prompt,
          sketchParameters,
        },
      })
    );
  }

  async function handleSketchFileChange(file: File | null) {
    if (sketchPreviewUrl) {
      URL.revokeObjectURL(sketchPreviewUrl);
    }

    if (!file) {
      setSketchFileName(null);
      setSketchPreviewUrl(null);
      setSketchParameters(null);
      setSketchUploadError(null);
      return;
    }

    setSketchFileName(file.name);
    setSketchPreviewUrl(URL.createObjectURL(file));
    setIsSketchUploading(true);
    setSketchUploadError(null);

    try {
      const form = new FormData();
      form.append("file", file);

      const response = await fetch(`${apiBase}/sketches/upload`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) {
        throw new Error(`Sketch upload failed: ${response.status}`);
      }

      const payload: SketchUploadResponse = await response.json();
      setSketchParameters(payload.extracted_parameters);
    } catch (error) {
      setSketchParameters(null);
      setSketchUploadError(error instanceof Error ? error.message : "Sketch upload failed");
    } finally {
      setIsSketchUploading(false);
    }
  }

  return (
    <main
      className={[
        "page",
        isLeftPanelCollapsed ? "page--left-collapsed" : "",
        isRightPanelCollapsed ? "page--right-collapsed" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <aside className={isLeftPanelCollapsed ? "left-panel left-panel--collapsed" : "left-panel"}>
        <button
          type="button"
          className="panel-collapse-toggle panel-collapse-toggle--left"
          onClick={() => setIsLeftPanelCollapsed((value) => !value)}
          aria-label={isLeftPanelCollapsed ? "Expand design brief panel" : "Collapse design brief panel"}
          aria-pressed={!isLeftPanelCollapsed}
        >
          {isLeftPanelCollapsed ? "»" : "«"}
        </button>

        <div className="panel-content">
        <h2>Design Brief</h2>
        <label className="upload-label">
          <span>Upload Sketch</span>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => handleSketchFileChange(e.target.files?.[0] ?? null)}
          />
        </label>
        {sketchFileName ? <p className="upload-meta">Sketch loaded: {sketchFileName}</p> : null}
        {isSketchUploading ? <p className="upload-meta">Analyzing sketch...</p> : null}
        {sketchUploadError ? <p className="error-hint">{sketchUploadError}</p> : null}
        {sketchPreviewUrl ? (
          <div className="sketch-preview-wrap">
            <img className="sketch-preview" src={sketchPreviewUrl} alt="Uploaded 2D sketch preview" />
          </div>
        ) : null}
        <label className="upload-label prompt-label">
          <span>Design Prompt</span>
          <textarea
            className="left-prompt-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
            placeholder="e.g. Vintage oval ruby ring with cathedral shank and halo accents"
          />
        </label>
        <div className="left-panel-actions">
          <button
            className="left-generate-btn"
            onClick={triggerPromptGeneration}
            disabled={isSketchUploading || (prompt.trim().length < 3 && !sketchParameters)}
          >
            Generate Jewelry
          </button>
        </div>
        </div>
      </aside>

      <section className="viewer viewer-canvas-only">
        <ViewerCanvas modelUrl={modelUrl} ringParameters={ringParameters} ringSummary={ringSummary} />
      </section>

      <aside className={isRightPanelCollapsed ? "right-panel right-panel--collapsed" : "right-panel"}>
        <button
          type="button"
          className="panel-collapse-toggle panel-collapse-toggle--right"
          onClick={() => setIsRightPanelCollapsed((value) => !value)}
          aria-label={isRightPanelCollapsed ? "Expand controls panel" : "Collapse controls panel"}
          aria-pressed={!isRightPanelCollapsed}
        >
          {isRightPanelCollapsed ? "«" : "»"}
        </button>

        <div className="panel-content">
        <RingWorkbench
          onViewerModelUrlChange={setModelUrl}
          onRingParametersChange={setRingParameters}
          onRingSummaryChange={setRingSummary}
          initialParameters={null}
          prompt={prompt}
          onPromptChange={setPrompt}
          hidePromptComposer
        />
        </div>
      </aside>
    </main>
  );
}
