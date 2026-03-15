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
        <h2>Design Prompt</h2>
        <p className="muted">
          Describe the ring style and components you want. Generation will create the base ring in the center canvas.
        </p>
        <label className="upload-label">
          <span>Upload 2D Sketch (Show Only)</span>
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
        <p className="muted">
          Sketch upload is for presentation only. The ring model is still generated from the prompt.
        </p>
        <label className="upload-label">
          <span>Prompt</span>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </label>
        <div className="export-row">
          <button onClick={triggerPromptGeneration} disabled={prompt.trim().length < 3}>
            Generate Ring
          </button>
        </div>
        <p className="muted">After generation, use the right panel to tweak components and apply change prompts.</p>
      </aside>

      <section className="viewer">
        <h1>JewelryAI MVP</h1>
        <p className="muted">Live canvas with immediate refresh on each customization change.</p>
        <ViewerCanvas modelUrl={modelUrl} ringParameters={ringParameters} />
      </section>

      <aside className="right-panel">
        <RingWorkbench
          onViewerModelUrlChange={setModelUrl}
          onRingParametersChange={setRingParameters}
          initialParameters={null}
          prompt={prompt}
          onPromptChange={setPrompt}
          hidePromptComposer
        />
      </aside>
    </main>
  );
}
