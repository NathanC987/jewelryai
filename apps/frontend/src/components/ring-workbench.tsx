"use client";

import { useEffect, useMemo, useState } from "react";

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
    setting_family: "basket" | "peghead" | "bezel" | "halo" | "cluster";
    setting_variant: number;
    setting_openheart: boolean;
    shank_family: "classic" | "cathedral" | "advanced";
    shank_variant: number;
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

type PromptRingResponse = {
  ring: RingState;
};

const apiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
const backendBase = apiBase.replace(/\/api\/v1\/?$/, "");

type RingWorkbenchProps = {
  onViewerModelUrlChange: (modelUrl: string | null) => void;
  onRingParametersChange?: (parameters: RingParameters | null) => void;
  onRingSummaryChange?: (
    summary:
      | {
          estimatedPriceUsd: number;
          manufacturabilityWarnings: { code: string; message: string }[];
        }
      | null
  ) => void;
  initialParameters?: Partial<RingParameters> | null;
  prompt: string;
  onPromptChange: (prompt: string) => void;
  hidePromptComposer?: boolean;
};

export function RingWorkbench({
  onViewerModelUrlChange,
  onRingParametersChange,
  onRingSummaryChange,
  initialParameters,
  prompt,
  onPromptChange,
  hidePromptComposer = false,
}: RingWorkbenchProps) {
  const [ring, setRing] = useState<RingState | null>(null);
  const [changePrompt, setChangePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingIntent, setLoadingIntent] = useState<
    "generating" | "updating" | "applying-change" | "exporting" | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const safePrompt = prompt ?? "";

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
    onViewerModelUrlChange(withCacheBust(absoluteUrl));
  }

  async function createRing() {
    setLoading(true);
    setLoadingIntent("generating");
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
      await refreshViewerModel(created.ring_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setLoadingIntent(null);
    }
  }

  async function createRingFromPrompt() {
    setLoading(true);
    setLoadingIntent("generating");
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
      setRing(payload.ring);
      await refreshViewerModel(payload.ring.ring_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setLoadingIntent(null);
    }
  }

  async function patchRing(update: Record<string, number | string | boolean>) {
    if (!ring) {
      return;
    }

    setLoading(true);
    setLoadingIntent("updating");
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
      setLoadingIntent(null);
    }
  }

  async function applyChangePrompt() {
    if (!ring) {
      return;
    }

    if (changePrompt.trim().length < 2) {
      return;
    }

    setLoading(true);
    setLoadingIntent("applying-change");
    setError(null);
    try {
      const response = await fetch(`${apiBase}/rings/${ring.ring_id}/change-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: changePrompt }),
      });
      if (!response.ok) {
        throw new Error(`Change prompt update failed: ${response.status}`);
      }

      const result = await response.json();
      setRing(result);
      setChangePrompt("");
      await refreshViewerModel(result.ring_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setLoadingIntent(null);
    }
  }

  useEffect(() => {
    onRingParametersChange?.(ring?.parameters ?? null);
  }, [onRingParametersChange, ring?.parameters]);

  useEffect(() => {
    onRingSummaryChange?.(
      ring
        ? {
            estimatedPriceUsd: ring.cost_estimate.estimated_price_usd,
            manufacturabilityWarnings: ring.manufacturability_warnings,
          }
        : null
    );
  }, [onRingSummaryChange, ring]);

  useEffect(() => {
    const handler = () => {
      void createRingFromPrompt();
    };
    window.addEventListener("ring-generate-from-prompt", handler);
    return () => window.removeEventListener("ring-generate-from-prompt", handler);
  });

  async function exportAndDownload(format: "glb" | "stl") {
    if (!ring) {
      return;
    }

    setLoading(true);
    setLoadingIntent("exporting");
    setError(null);
    try {
      const response = await fetch(`${apiBase}/exports/${ring.ring_id}/${format}`);
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }

      const result = await response.json();
      const absoluteUrl = toAbsoluteArtifactUrl(result.artifact_uri);
      const fileResponse = await fetch(absoluteUrl);
      if (!fileResponse.ok) {
        throw new Error(`Download failed: ${fileResponse.status}`);
      }

      const fileBlob = await fileResponse.blob();
      const objectUrl = URL.createObjectURL(fileBlob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = `ring-${ring.ring_id}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setLoadingIntent(null);
    }
  }

  const loadingLabel =
    loadingIntent === "generating"
      ? "Generating your ring design..."
      : loadingIntent === "updating"
        ? "Updating ring details..."
        : loadingIntent === "applying-change"
          ? "Applying change prompt..."
          : loadingIntent === "exporting"
            ? "Preparing export file..."
            : null;

  return (
    <div className="workbench">
      {loading && loadingLabel ? (
        <div className="status-banner" role="status" aria-live="polite">
          <span className="status-dot" aria-hidden="true" />
          <p>{loadingLabel}</p>
        </div>
      ) : null}

      <section className="change-prompt-card">
        <h3>Quick Change Prompt</h3>
        <p className="muted">Describe a design change in plain language and apply it to the current ring.</p>
        <label className="change-prompt-label">
          <textarea
            disabled={!canEdit || loading}
            value={changePrompt}
            onChange={(e) => setChangePrompt(e.target.value)}
            rows={4}
            placeholder="e.g. switch to marquise bezel with cathedral shank"
          />
        </label>
        <button
          disabled={!canEdit || loading || changePrompt.trim().length < 2}
          onClick={() => void applyChangePrompt()}
        >
          Apply Change Prompt
        </button>
      </section>

      {!hidePromptComposer ? (
        <section className="result">
          <h3>Prompt Studio</h3>
          <p className="muted">Create a new ring directly from your design prompt.</p>
          <label>
            Design Prompt
            <input
              type="text"
              disabled={loading}
              value={safePrompt}
              onChange={(e) => onPromptChange(e.target.value)}
            />
          </label>
          <div className="export-row">
            <button onClick={createRingFromPrompt} disabled={loading || safePrompt.trim().length < 3}>
              {ring ? "Regenerate From Prompt" : "Generate From Prompt"}
            </button>
            <button onClick={createRing} disabled={loading}>
              Create From Seeded Parameters
            </button>
          </div>
        </section>
      ) : null}

      <section className="workbench-group">
        <div className="group-header">
          <h3>Core Style</h3>
          <p className="muted">Choose your metal, gemstone, and center stone silhouette.</p>
        </div>
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
        </div>
      </section>

      <section className="workbench-group">
        <div className="group-header">
          <h3>Setting and Structure</h3>
          <p className="muted">Refine architecture details for setting, shank, and profile.</p>
        </div>
        <div className="controls">
          <label>
            Setting Family
            <select
              disabled={!canEdit || loading}
              value={ring?.parameters.setting_family ?? "peghead"}
              onChange={(e) => patchRing({ setting_family: e.target.value })}
            >
              <option value="peghead">Peghead</option>
              <option value="basket">Basket</option>
              <option value="bezel">Bezel</option>
              <option value="halo">Halo</option>
              <option value="cluster">Cluster</option>
            </select>
          </label>

          <label>
            Setting Variant
            <input
              type="number"
              min={1}
              max={20}
              step={1}
              disabled={!canEdit || loading}
              value={ring?.parameters.setting_variant ?? 4}
              onChange={(e) => patchRing({ setting_variant: Number.parseInt(e.target.value, 10) })}
            />
            <span className="field-hint">Range: 1-20</span>
          </label>

          <label>
            Open Heart
            <select
              disabled={!canEdit || loading}
              value={ring?.parameters.setting_openheart ? "yes" : "no"}
              onChange={(e) => patchRing({ setting_openheart: e.target.value === "yes" })}
            >
              <option value="no">No</option>
              <option value="yes">Yes</option>
            </select>
          </label>

          <label>
            Shank Family
            <select
              disabled={!canEdit || loading}
              value={ring?.parameters.shank_family ?? "classic"}
              onChange={(e) => patchRing({ shank_family: e.target.value })}
            >
              <option value="classic">Classic</option>
              <option value="cathedral">Cathedral</option>
              <option value="advanced">Advanced</option>
            </select>
          </label>

          <label>
            Shank Variant
            <input
              type="number"
              min={1}
              max={20}
              step={1}
              disabled={!canEdit || loading}
              value={ring?.parameters.shank_variant ?? 1}
              onChange={(e) => patchRing({ shank_variant: Number.parseInt(e.target.value, 10) })}
            />
            <span className="field-hint">Range: 1-20</span>
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
        </div>
      </section>

      <section className="workbench-group">
        <div className="group-header">
          <h3>Dimensions</h3>
          <p className="muted">Adjust measurable proportions used in manufacturing output.</p>
        </div>
        <div className="controls">
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
            <span className="field-hint">Range: 2-8</span>
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
            <span className="field-hint">Range: 0-24</span>
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
            <span className="field-hint">Range: 0.6-5.0 mm</span>
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
            <span className="field-hint">Range: 1.0-12.0 mm</span>
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
            <span className="field-hint">Range: 1.2-5.0 mm</span>
          </label>
        </div>
      </section>

      {error ? (
        <div className="error" role="alert">
          <p>{error}</p>
          <p className="error-hint">Try your action again. If this persists, regenerate and retry.</p>
        </div>
      ) : null}

      {ring ? (
        <div className="export-section">
          <p><strong>Exports</strong></p>
          <p className="muted">Download high-fidelity files for viewing and production.</p>
          <div className="export-row export-row-vertical">
            <button disabled={!canEdit || loading} onClick={() => exportAndDownload("glb")}>Export GLB</button>
            <button disabled={!canEdit || loading} onClick={() => exportAndDownload("stl")}>Export STL</button>
          </div>
        </div>
      ) : (
        <p className="muted">Create a jewelry to enable customization.</p>
      )}
    </div>
  );
}
