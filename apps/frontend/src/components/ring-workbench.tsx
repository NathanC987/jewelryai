"use client";

import { useMemo, useState } from "react";

type RingState = {
  ring_id: string;
  parameters: {
    template_id: "solitaire_ring" | "halo_ring" | "pave_band_ring" | "split_shank_ring" | "three_stone_ring";
    style_tag: "modern" | "vintage" | "royal" | "minimalist";
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
  cost_estimate: {
    metal_weight_g: number;
    gemstone_carat: number;
    estimated_price_usd: number;
  };
  manufacturability_warnings: { code: string; message: string }[];
  glb_asset_uri: string;
};

type RingParameters = RingState["parameters"];

type VariationSuggestion = {
  style_name: string;
  summary: string;
  ring: RingState;
};

type PromptInterpretation = {
  normalized_prompt: string;
  template_id: RingState["parameters"]["template_id"];
  style_tag: RingState["parameters"]["style_tag"];
  selected_components: string[];
  confidence: number;
  notes: string;
};

type PromptRingResponse = {
  interpretation: PromptInterpretation;
  ring: RingState;
};

const apiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
const backendBase = apiBase.replace(/\/api\/v1\/?$/, "");

type RingWorkbenchProps = {
  onViewerModelUrlChange: (modelUrl: string | null) => void;
  initialParameters?: Partial<RingParameters> | null;
};

export function RingWorkbench({ onViewerModelUrlChange, initialParameters }: RingWorkbenchProps) {
  const [ring, setRing] = useState<RingState | null>(null);
  const [prompt, setPrompt] = useState("A modern solitaire diamond ring with a clean silhouette");
  const [interpretation, setInterpretation] = useState<PromptInterpretation | null>(null);
  const [variations, setVariations] = useState<VariationSuggestion[]>([]);
  const [exportLinks, setExportLinks] = useState<{ glb?: string; stl?: string }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canEdit = useMemo(() => Boolean(ring?.ring_id), [ring?.ring_id]);

  function toAbsoluteArtifactUrl(artifactUri: string): string {
    return `${backendBase}${artifactUri}`;
  }

  function withCacheBust(url: string): string {
    const separator = url.includes("?") ? "&" : "?";
    return `${url}${separator}v=${Date.now()}`;
  }

  async function refreshViewerModel(ringId: string): Promise<void> {
    const response = await fetch(`${apiBase}/exports/${ringId}/glb`);
    if (!response.ok) {
      throw new Error(`Viewer GLB refresh failed: ${response.status}`);
    }

    const exportResult = await response.json();
    const absoluteUrl = toAbsoluteArtifactUrl(exportResult.artifact_uri);
    setExportLinks((prev) => ({ ...prev, glb: absoluteUrl }));
    onViewerModelUrlChange(withCacheBust(absoluteUrl));
  }

  async function createRing() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/rings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: initialParameters ? JSON.stringify(initialParameters) : undefined,
      });
      if (!response.ok) {
        throw new Error(`Create failed: ${response.status}`);
      }
      const created = await response.json();
      setRing(created);
      setInterpretation(null);
      setVariations([]);
      await refreshViewerModel(created.ring_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function createRingFromPrompt() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/rings/from-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!response.ok) {
        throw new Error(`Prompt generation failed: ${response.status}`);
      }

      const payload: PromptRingResponse = await response.json();
      setInterpretation(payload.interpretation);
      setRing(payload.ring);
      setVariations([]);
      await refreshViewerModel(payload.ring.ring_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function patchRing(update: Record<string, number | string>) {
    if (!ring) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/rings/${ring.ring_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(update),
      });
      if (!response.ok) {
        throw new Error(`Update failed: ${response.status}`);
      }
      const patched = await response.json();
      setRing(patched);
      await refreshViewerModel(patched.ring_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function generateVariations() {
    if (!ring) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/rings/${ring.ring_id}/variations?count=5`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`Variation generation failed: ${response.status}`);
      }

      const result = await response.json();
      setVariations(result.suggestions ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function activateVariation(suggestion: VariationSuggestion) {
    setRing(suggestion.ring);
    setExportLinks({});
    await refreshViewerModel(suggestion.ring.ring_id);
  }

  async function requestExport(format: "glb" | "stl") {
    if (!ring) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/exports/${ring.ring_id}/${format}`);
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }

      const result = await response.json();
      const absoluteUrl = toAbsoluteArtifactUrl(result.artifact_uri);
      setExportLinks((prev) => ({ ...prev, [format]: absoluteUrl }));
      if (format === "glb") {
        onViewerModelUrlChange(withCacheBust(absoluteUrl));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="workbench">
      <div className="result">
        <p><strong>Prompt-First Designer</strong></p>
        <p className="muted">Describe the ring you want. This is the default generation path.</p>
        <label>
          Design Prompt
          <input
            type="text"
            disabled={loading}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </label>
        <div className="export-row">
          <button onClick={createRingFromPrompt} disabled={loading || prompt.trim().length < 3}>
            {ring ? "Regenerate From Prompt" : "Generate From Prompt"}
          </button>
          <button onClick={createRing} disabled={loading}>
            Create From Seeded Parameters
          </button>
        </div>
      </div>

      {interpretation ? (
        <div className="result">
          <p><strong>Prompt Interpretation</strong></p>
          <p>Template: {interpretation.template_id.replace(/_/g, " ")}</p>
          <p>Style: {interpretation.style_tag}</p>
          <p>Components: {interpretation.selected_components.join(" | ")}</p>
          <p>Confidence: {(interpretation.confidence * 100).toFixed(0)}%</p>
          <p className="muted">{interpretation.notes}</p>
        </div>
      ) : null}

      <div className="controls">
        <label>
          Metal
          <select
            disabled={!canEdit || loading}
            value={ring?.parameters.metal ?? "gold"}
            onChange={(e) => patchRing({ metal: e.target.value })}
          >
            <option value="gold">Gold</option>
            <option value="rose_gold">Rose Gold</option>
            <option value="platinum">Platinum</option>
            <option value="silver">Silver</option>
          </select>
        </label>

        <label>
          Gemstone
          <select
            disabled={!canEdit || loading}
            value={ring?.parameters.gemstone_type ?? "diamond"}
            onChange={(e) => patchRing({ gemstone_type: e.target.value })}
          >
            <option value="diamond">Diamond</option>
            <option value="ruby">Ruby</option>
            <option value="emerald">Emerald</option>
            <option value="sapphire">Sapphire</option>
          </select>
        </label>

        <label>
          Stone Shape
          <select
            disabled={!canEdit || loading}
            value={ring?.parameters.center_stone_shape ?? "round"}
            onChange={(e) => patchRing({ center_stone_shape: e.target.value })}
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
            disabled={!canEdit || loading}
            value={ring?.parameters.prong_count ?? 4}
            onChange={(e) => patchRing({ prong_count: Number.parseInt(e.target.value, 10) })}
          />
        </label>

        <label>
          Band Profile
          <select
            disabled={!canEdit || loading}
            value={ring?.parameters.band_profile ?? "classic"}
            onChange={(e) => patchRing({ band_profile: e.target.value })}
          >
            <option value="classic">Classic</option>
            <option value="flat">Flat</option>
            <option value="knife_edge">Knife Edge</option>
            <option value="tapered">Tapered</option>
          </select>
        </label>

        <label>
          Side Stone Count
          <input
            type="number"
            min={0}
            max={24}
            step={1}
            disabled={!canEdit || loading}
            value={ring?.parameters.side_stone_count ?? 0}
            onChange={(e) => patchRing({ side_stone_count: Number.parseInt(e.target.value, 10) })}
          />
        </label>

        <label>
          Setting Height (mm)
          <input
            type="number"
            min={0.6}
            max={5}
            step={0.1}
            disabled={!canEdit || loading}
            value={ring?.parameters.setting_height_mm ?? 1.8}
            onChange={(e) => patchRing({ setting_height_mm: Number.parseFloat(e.target.value) })}
          />
        </label>

        <label>
          Gem Size (mm)
          <input
            type="number"
            min={1}
            max={12}
            step={0.1}
            disabled={!canEdit || loading}
            value={ring?.parameters.gemstone_size_mm ?? 4}
            onChange={(e) =>
              patchRing({ gemstone_size_mm: Number.parseFloat(e.target.value) })
            }
          />
        </label>

        <label>
          Band Thickness (mm)
          <input
            type="number"
            min={1.2}
            max={5}
            step={0.1}
            disabled={!canEdit || loading}
            value={ring?.parameters.band_thickness_mm ?? 2}
            onChange={(e) =>
              patchRing({ band_thickness_mm: Number.parseFloat(e.target.value) })
            }
          />
        </label>
      </div>

      {error ? <p className="error">{error}</p> : null}

      {ring ? (
        <div className="result">
          <p>
            Estimated Price: ${ring.cost_estimate.estimated_price_usd.toFixed(2)}
          </p>
          <p>
            Metal Weight: {ring.cost_estimate.metal_weight_g}g | Gemstone: {" "}
            {ring.cost_estimate.gemstone_carat}ct
          </p>
          <p>
            Shape: {ring.parameters.center_stone_shape.replace("_", " ")} | Prongs: {ring.parameters.prong_count} | Side Stones: {ring.parameters.side_stone_count} | Profile: {ring.parameters.band_profile.replace("_", " ")} | Setting: {ring.parameters.setting_height_mm} mm
          </p>
          <p>
            Template: {ring.parameters.template_id.replace(/_/g, " ")} | Style: {ring.parameters.style_tag}
          </p>
          <p>GLB URI: {ring.glb_asset_uri}</p>
          <div className="export-row">
            <button disabled={loading} onClick={() => requestExport("glb")}>Request GLB Export</button>
            <button disabled={loading} onClick={() => requestExport("stl")}>Request STL Export</button>
            <button disabled={loading} onClick={generateVariations}>Generate 5 Style Variations</button>
          </div>
          {exportLinks.glb ? <p>GLB Export: {exportLinks.glb}</p> : null}
          {exportLinks.stl ? <p>STL Export: {exportLinks.stl}</p> : null}
          {ring.manufacturability_warnings.length > 0 ? (
            <ul>
              {ring.manufacturability_warnings.map((warning) => (
                <li key={warning.code}>{warning.message}</li>
              ))}
            </ul>
          ) : (
            <p>No manufacturability warnings.</p>
          )}

          {variations.length > 0 ? (
            <div className="variations-block">
              <p><strong>Variation Concepts</strong></p>
              <div className="variation-grid">
                {variations.map((suggestion) => (
                  <div className="variation-card" key={suggestion.ring.ring_id}>
                    <p><strong>{suggestion.style_name}</strong></p>
                    <p>{suggestion.summary}</p>
                    <p>
                      {suggestion.ring.parameters.gemstone_type} / {suggestion.ring.parameters.center_stone_shape.replace("_", " ")}
                    </p>
                    <p>
                      ${suggestion.ring.cost_estimate.estimated_price_usd.toFixed(2)}
                    </p>
                    <button disabled={loading} onClick={() => void activateVariation(suggestion)}>
                      Use This Variant
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        <p className="muted">Create a ring to enable customization.</p>
      )}
    </div>
  );
}
