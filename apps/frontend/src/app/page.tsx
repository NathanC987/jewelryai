"use client";

import { useEffect, useState } from "react";

import { RingWorkbench } from "../components/ring-workbench";
import { ViewerCanvas } from "../components/viewer-canvas";

export default function HomePage() {
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [sketchFileName, setSketchFileName] = useState<string | null>(null);
  const [sketchPreviewUrl, setSketchPreviewUrl] = useState<string | null>(null);
  const [ringParameters, setRingParameters] = useState<{
    metal: "gold" | "rose_gold" | "platinum" | "silver";
    gemstone_type: "diamond" | "ruby" | "emerald" | "sapphire";
  } | null>(null);
  const [ringSummary, setRingSummary] = useState<{
    estimatedPriceUsd: number;
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
    window.dispatchEvent(new Event("ring-generate-from-prompt"));
  }

  function handleSketchFileChange(file: File | null) {
    if (sketchPreviewUrl) {
      URL.revokeObjectURL(sketchPreviewUrl);
    }

    if (!file) {
      setSketchFileName(null);
      setSketchPreviewUrl(null);
      return;
    }

    setSketchFileName(file.name);
    setSketchPreviewUrl(URL.createObjectURL(file));
  }

  return (
    <main className="page">
      <aside className="left-panel">
        <h2>Design Options</h2>
        <p className="muted">
          Upload a 2D sketch of your design or describe the jewelry design you want.
        </p>
        <label className="upload-label">
          <span>Upload 2D Sketch</span>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => handleSketchFileChange(e.target.files?.[0] ?? null)}
          />
        </label>
        {sketchFileName ? <p className="upload-meta">Sketch loaded: {sketchFileName}</p> : null}
        {sketchPreviewUrl ? (
          <div className="sketch-preview-wrap">
            <img className="sketch-preview" src={sketchPreviewUrl} alt="Uploaded 2D sketch preview" />
          </div>
        ) : null}
        <label className="upload-label prompt-label">
          <span>Prompt</span>
          <textarea
            className="left-prompt-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            placeholder="e.g. Vintage oval ruby ring with cathedral shank and halo accents"
          />
        </label>
        <div className="left-panel-actions">
          <button className="left-generate-btn" onClick={triggerPromptGeneration} disabled={prompt.trim().length < 3}>
            Generate Jewelry
          </button>
        </div>
        <p className="muted">After generation, use the right panel to tweak components and apply change prompts.</p>
      </aside>

      <section className="viewer viewer-canvas-only">
        <ViewerCanvas modelUrl={modelUrl} ringParameters={ringParameters} ringSummary={ringSummary} />
      </section>

      <aside className="right-panel">
        <RingWorkbench
          onViewerModelUrlChange={setModelUrl}
          onRingParametersChange={setRingParameters}
          onRingSummaryChange={setRingSummary}
          initialParameters={null}
          prompt={prompt}
          onPromptChange={setPrompt}
          hidePromptComposer
        />
      </aside>
    </main>
  );
}
