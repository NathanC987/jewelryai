"use client";

import { useEffect, useState } from "react";
import Image from "next/image";

import { RingWorkbench } from "../components/ring-workbench";
import { ViewerCanvas } from "../components/viewer-canvas";

type ExtractedParameters = {
  metal: "gold" | "rose_gold" | "platinum" | "silver";
  gemstone_type: "diamond" | "ruby" | "emerald" | "sapphire";
  center_stone_shape: "round" | "oval" | "princess" | "emerald_cut" | "marquise" | "pear";
  prong_count: number;
  band_profile: "classic" | "flat" | "knife_edge" | "tapered";
  side_stone_count: number;
  setting_height_mm: number;
  gemstone_size_mm: number;
  band_thickness_mm: number;
};

type SketchAnalysis = {
  sketch_id: string;
  components: { component_type: string; confidence: number }[];
  feature_confidences: { feature_name: string; confidence: number }[];
  requires_user_confirmation: boolean;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export default function HomePage() {
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [sketchName, setSketchName] = useState<string | null>(null);
  const [sketchPreviewUrl, setSketchPreviewUrl] = useState<string | null>(null);
  const [extractedParams, setExtractedParams] = useState<ExtractedParameters | null>(null);
  const [confirmedParams, setConfirmedParams] = useState<ExtractedParameters | null>(null);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "ready" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState<string>("No sketch uploaded yet.");
  const [analysis, setAnalysis] = useState<SketchAnalysis | null>(null);

  function updateDraftParam<K extends keyof ExtractedParameters>(key: K, value: ExtractedParameters[K]) {
    setExtractedParams((prev) => {
      if (!prev) {
        return prev;
      }
      return { ...prev, [key]: value };
    });
  }

  useEffect(() => {
    return () => {
      if (sketchPreviewUrl) {
        URL.revokeObjectURL(sketchPreviewUrl);
      }
    };
  }, [sketchPreviewUrl]);

  async function onSketchSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0];
    if (!nextFile) {
      return;
    }

    if (sketchPreviewUrl) {
      URL.revokeObjectURL(sketchPreviewUrl);
    }

    setSketchName(nextFile.name);
    setSketchPreviewUrl(URL.createObjectURL(nextFile));

    try {
      setUploadState("uploading");
      setUploadMessage("Uploading sketch and extracting initial parameters...");

      const formData = new FormData();
      formData.append("file", nextFile);

      const response = await fetch(`${apiBase}/sketches/upload`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`Sketch upload failed: ${response.status}`);
      }

      const result = await response.json();
      setExtractedParams(result.extracted_parameters);
      setConfirmedParams(null);

      const analysisResponse = await fetch(`${apiBase}/sketches/${result.sketch_id}/analysis`);
      if (!analysisResponse.ok) {
        throw new Error(`Sketch analysis failed: ${analysisResponse.status}`);
      }
      const analysisResult = await analysisResponse.json();
      setAnalysis(analysisResult);

      if (!analysisResult.requires_user_confirmation) {
        setConfirmedParams(result.extracted_parameters);
      }

      setUploadState("ready");
      setUploadMessage(result.extraction_note);
    } catch (error) {
      setUploadState("error");
      setUploadMessage(error instanceof Error ? error.message : "Sketch upload failed.");
      setExtractedParams(null);
      setConfirmedParams(null);
      setAnalysis(null);
    }
  }

  return (
    <main className="page">
      <aside className="left-panel">
        <h2>Sketch Input (Experimental)</h2>
        <p className="muted">
          Prompt-first generation is now the primary flow. Uploading sketches remains available as an experimental seed path.
        </p>
        <label className="upload-label">
          <span>Sketch File</span>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={onSketchSelected}
          />
        </label>
        {sketchName ? <p className="upload-meta">Loaded: {sketchName}</p> : null}
        {sketchPreviewUrl ? (
          <div className="sketch-preview-wrap">
            <Image
              src={sketchPreviewUrl}
              alt="Uploaded sketch preview"
              className="sketch-preview"
              width={640}
              height={480}
            />
          </div>
        ) : (
          <p className="muted">No sketch uploaded yet.</p>
        )}
        <p className={uploadState === "error" ? "error" : "muted"}>{uploadMessage}</p>
        {extractedParams ? (
          <div className="result">
            <p><strong>Extracted Seed</strong></p>
            <p>Metal: {extractedParams.metal.replace("_", " ")}</p>
            <p>
              Gem: {extractedParams.gemstone_type} / {extractedParams.center_stone_shape.replace("_", " ")} ({extractedParams.gemstone_size_mm} mm)
            </p>
            <p>Prongs: {extractedParams.prong_count}</p>
            <p>Side Stones: {extractedParams.side_stone_count}</p>
            <p>Setting Height: {extractedParams.setting_height_mm} mm</p>
            <p>Band Profile: {extractedParams.band_profile.replace("_", " ")}</p>
            <p>Band Thickness: {extractedParams.band_thickness_mm} mm</p>
          </div>
        ) : null}

        {analysis ? (
          <div className="result">
            <p><strong>Analysis Confidence</strong></p>
            {analysis.components.map((component) => (
              <p key={component.component_type}>
                {component.component_type.replace("_", " ")}: {(component.confidence * 100).toFixed(0)}%
              </p>
            ))}
            <p className={analysis.requires_user_confirmation ? "error" : "muted"}>
              {analysis.requires_user_confirmation
                ? "Low-confidence features detected. Review and confirm extracted features before creating the 3D ring."
                : "Confidence levels are stable for initial sketch interpretation."}
            </p>

            {extractedParams ? (
              <div className="controls">
                <label>
                  Stone Shape
                  <select
                    value={extractedParams.center_stone_shape}
                    onChange={(e) => updateDraftParam("center_stone_shape", e.target.value as ExtractedParameters["center_stone_shape"])}
                  >
                    <option value="round">Round</option>
                    <option value="oval">Oval</option>
                    <option value="princess">Princess</option>
                    <option value="emerald_cut">Emerald Cut</option>
                    <option value="marquise">Marquise</option>
                    <option value="pear">Pear</option>
                  </select>
                </label>

                <label>
                  Prong Count
                  <input
                    type="number"
                    min={2}
                    max={8}
                    step={1}
                    value={extractedParams.prong_count}
                    onChange={(e) => updateDraftParam("prong_count", Number.parseInt(e.target.value, 10))}
                  />
                </label>

                <label>
                  Side Stone Count
                  <input
                    type="number"
                    min={0}
                    max={24}
                    step={1}
                    value={extractedParams.side_stone_count}
                    onChange={(e) => updateDraftParam("side_stone_count", Number.parseInt(e.target.value, 10))}
                  />
                </label>

                <label>
                  Setting Height (mm)
                  <input
                    type="number"
                    min={0.6}
                    max={5}
                    step={0.1}
                    value={extractedParams.setting_height_mm}
                    onChange={(e) => updateDraftParam("setting_height_mm", Number.parseFloat(e.target.value))}
                  />
                </label>

                <button onClick={() => setConfirmedParams(extractedParams)}>
                  Confirm Features For 3D Generation
                </button>
              </div>
            ) : null}

            {confirmedParams ? (
              <p className="muted">Feature seed confirmed and ready for Create From Seeded Parameters.</p>
            ) : null}
          </div>
        ) : null}
      </aside>

      <section className="viewer">
        <h1>JewelryAI MVP</h1>
        <p className="muted">Default flow: generate polished template-based rings from prompt, then refine with controls.</p>
        <ViewerCanvas modelUrl={modelUrl} />
      </section>

      <aside className="right-panel">
        <RingWorkbench
          onViewerModelUrlChange={setModelUrl}
          initialParameters={confirmedParams}
        />
      </aside>
    </main>
  );
}
