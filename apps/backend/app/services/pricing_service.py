from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from math import pi
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from app.core.config import settings
from app.domain.ring import CostEstimate, CostLineItem, RingParameters


logger = logging.getLogger("service.pricing")


BASELINE_METAL_RATES_USD_PER_G = {
    "gold": 85.0,
    "rose_gold": 88.0,
    "platinum": 65.0,
    "silver": 2.0,
}

BASELINE_GEMSTONE_RATES_USD_PER_CARAT = {
    "diamond": 1200.0,
    "ruby": 650.0,
    "emerald": 550.0,
    "sapphire": 500.0,
}

# Densities in g/cm^3 for rough mass estimation from parametric geometry.
METAL_DENSITY_G_PER_CM3 = {
    "gold": 19.32,
    "rose_gold": 18.0,
    "platinum": 21.45,
    "silver": 10.49,
}

GEMSTONE_DENSITY_G_PER_CM3 = {
    "diamond": 3.52,
    "ruby": 4.0,
    "emerald": 2.76,
    "sapphire": 4.0,
}


@dataclass
class MarketRatesSnapshot:
    metal_rates_usd_per_g: dict[str, float]
    gemstone_rates_usd_per_carat: dict[str, float]
    source: str
    fetched_at: datetime


class PricingService:
    def __init__(self) -> None:
        self._snapshot: MarketRatesSnapshot | None = None

    def estimate_cost(self, params: RingParameters) -> CostEstimate:
        rates = self._get_rates()
        metal_weight_g = round(_estimate_metal_weight_g(params), 3)
        center_stone_carat = round(_estimate_center_stone_carat(params), 3)
        side_stone_carat = round(_estimate_side_stones_carat(params), 3)

        metal_rate = rates.metal_rates_usd_per_g[params.metal]
        gemstone_rate = rates.gemstone_rates_usd_per_carat[params.gemstone_type]

        shank_multiplier = {
            "classic": 1.0,
            "cathedral": 1.08,
            "advanced": 1.15,
        }[params.shank_family]
        setting_multiplier = {
            "peghead": 1.0,
            "basket": 1.04,
            "bezel": 1.06,
            "halo": 1.1,
            "cluster": 1.12,
        }[params.setting_family]

        metal_subtotal = round(metal_weight_g * metal_rate * shank_multiplier, 2)
        center_subtotal = round(center_stone_carat * gemstone_rate, 2)
        side_subtotal = round(side_stone_carat * gemstone_rate * 0.45 * setting_multiplier, 2)
        estimated_price = round(metal_subtotal + center_subtotal + side_subtotal, 2)

        rates_age_seconds = max(0, int((datetime.now(timezone.utc) - rates.fetched_at).total_seconds()))

        return CostEstimate(
            metal_weight_g=metal_weight_g,
            gemstone_carat=center_stone_carat,
            side_stone_carat=side_stone_carat,
            estimated_price_usd=estimated_price,
            pricing_source=_normalize_source(rates.source),
            rates_timestamp_utc=rates.fetched_at.isoformat(),
            rates_age_seconds=rates_age_seconds,
            line_items=[
                CostLineItem(
                    label="Metal",
                    quantity=round(metal_weight_g, 3),
                    unit="g",
                    unit_price_usd=round(metal_rate * shank_multiplier, 3),
                    subtotal_usd=metal_subtotal,
                ),
                CostLineItem(
                    label="Center Stone",
                    quantity=round(center_stone_carat, 3),
                    unit="ct",
                    unit_price_usd=round(gemstone_rate, 3),
                    subtotal_usd=center_subtotal,
                ),
                CostLineItem(
                    label="Side Stones",
                    quantity=round(side_stone_carat, 3),
                    unit="ct",
                    unit_price_usd=round(gemstone_rate * 0.45 * setting_multiplier, 3),
                    subtotal_usd=side_subtotal,
                ),
            ],
        )

    def _get_rates(self) -> MarketRatesSnapshot:
        refresh_seconds = max(60, settings.pricing_market_refresh_seconds)
        now = datetime.now(timezone.utc)

        if self._snapshot is not None:
            age = (now - self._snapshot.fetched_at).total_seconds()
            if age < refresh_seconds:
                return self._snapshot

        if settings.pricing_market_enabled:
            live_snapshot = self._fetch_live_snapshot()
            if live_snapshot is not None:
                self._snapshot = live_snapshot
                self._persist_cache(live_snapshot)
                return live_snapshot

        cached_snapshot = self._load_cache()
        if cached_snapshot is not None:
            self._snapshot = cached_snapshot
            return cached_snapshot

        baseline = MarketRatesSnapshot(
            metal_rates_usd_per_g=BASELINE_METAL_RATES_USD_PER_G.copy(),
            gemstone_rates_usd_per_carat=BASELINE_GEMSTONE_RATES_USD_PER_CARAT.copy(),
            source="baseline",
            fetched_at=now,
        )
        self._snapshot = baseline
        logger.warning({"operation": "pricing_rates", "status": "baseline_fallback"})
        return baseline

    def _fetch_live_snapshot(self) -> MarketRatesSnapshot | None:
        metals = _fetch_metal_rates(settings.pricing_metals_api_url, settings.pricing_market_timeout_seconds)
        if not metals:
            logger.warning({"operation": "pricing_rates_fetch", "status": "failed", "provider": "metals"})
            return None

        gemstones = _fetch_gemstone_rates(
            settings.pricing_gemstones_api_url,
            settings.pricing_market_timeout_seconds,
        ) or BASELINE_GEMSTONE_RATES_USD_PER_CARAT.copy()

        snapshot = MarketRatesSnapshot(
            metal_rates_usd_per_g={**BASELINE_METAL_RATES_USD_PER_G, **metals},
            gemstone_rates_usd_per_carat={**BASELINE_GEMSTONE_RATES_USD_PER_CARAT, **gemstones},
            source="live",
            fetched_at=datetime.now(timezone.utc),
        )
        logger.info(
            {
                "operation": "pricing_rates_fetch",
                "status": "success",
                "metal_rates": snapshot.metal_rates_usd_per_g,
                "gemstone_rates": snapshot.gemstone_rates_usd_per_carat,
            }
        )
        return snapshot

    def _cache_file(self) -> Path:
        if settings.pricing_market_cache_path:
            return Path(settings.pricing_market_cache_path)
        return Path(__file__).resolve().parents[2] / "artifacts" / "market_rates_cache.json"

    def _persist_cache(self, snapshot: MarketRatesSnapshot) -> None:
        cache_file = self._cache_file()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": snapshot.source,
            "fetched_at": snapshot.fetched_at.isoformat(),
            "metal_rates_usd_per_g": snapshot.metal_rates_usd_per_g,
            "gemstone_rates_usd_per_carat": snapshot.gemstone_rates_usd_per_carat,
        }
        cache_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _load_cache(self) -> MarketRatesSnapshot | None:
        cache_file = self._cache_file()
        if not cache_file.exists():
            return None
        try:
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(str(payload["fetched_at"]).replace("Z", "+00:00"))
            source = "cached"
            return MarketRatesSnapshot(
                metal_rates_usd_per_g={
                    **BASELINE_METAL_RATES_USD_PER_G,
                    **payload.get("metal_rates_usd_per_g", {}),
                },
                gemstone_rates_usd_per_carat={
                    **BASELINE_GEMSTONE_RATES_USD_PER_CARAT,
                    **payload.get("gemstone_rates_usd_per_carat", {}),
                },
                source=source,
                fetched_at=fetched_at,
            )
        except Exception as exc:
            logger.warning({"operation": "pricing_rates_cache_load", "status": "failed", "error": str(exc)})
            return None


def _normalize_source(source: str) -> str:
    if source == "live":
        return "live"
    if source == "cached":
        return "cached"
    return "baseline"


def _fetch_json(url: str, timeout_seconds: float) -> object | None:
    try:
        with urlopen(url, timeout=timeout_seconds) as response:  # nosec B310 - URL is controlled by app config.
            return json.loads(response.read().decode("utf-8"))
    except (URLError, ValueError, TimeoutError):
        return None


def _fetch_metal_rates(url: str, timeout_seconds: float) -> dict[str, float] | None:
    payload = _fetch_json(url, timeout_seconds)
    if not isinstance(payload, list):
        return None

    # metals.live returns values in USD per troy ounce.
    ounce_values: dict[str, float] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            if isinstance(value, (int, float)):
                ounce_values[key.lower()] = float(value)

    gold_oz = ounce_values.get("gold") or ounce_values.get("xau")
    silver_oz = ounce_values.get("silver") or ounce_values.get("xag")
    platinum_oz = ounce_values.get("platinum") or ounce_values.get("xpt")

    converted: dict[str, float] = {}
    if gold_oz:
        converted["gold"] = round(gold_oz / 31.1034768, 3)
        converted["rose_gold"] = round(converted["gold"] * 1.035, 3)
    if silver_oz:
        converted["silver"] = round(silver_oz / 31.1034768, 3)
    if platinum_oz:
        converted["platinum"] = round(platinum_oz / 31.1034768, 3)

    return converted or None


def _fetch_gemstone_rates(url: str | None, timeout_seconds: float) -> dict[str, float] | None:
    if not url:
        return None

    payload = _fetch_json(url, timeout_seconds)
    if not isinstance(payload, dict):
        return None

    parsed: dict[str, float] = {}
    for gemstone in ("diamond", "ruby", "emerald", "sapphire"):
        value = payload.get(gemstone)
        if isinstance(value, (int, float)):
            parsed[gemstone] = float(value)

    return parsed or None


def _estimate_metal_weight_g(params: RingParameters) -> float:
    # Fast analytical approximation of a ring band volume from parametric controls.
    profile_factor = {
        "classic": 0.78,
        "flat": 0.92,
        "knife_edge": 0.62,
        "tapered": 0.71,
    }[params.band_profile]
    shank_factor = {
        "classic": 1.0,
        "cathedral": 1.08,
        "advanced": 1.14,
    }[params.shank_family]

    inner_radius_mm = 8.7
    band_width_mm = 1.8 + params.setting_height_mm * 0.18 + params.side_stone_count * 0.03
    cross_section_area_mm2 = max(0.4, params.band_thickness_mm * band_width_mm * profile_factor)
    centerline_radius_mm = inner_radius_mm + params.band_thickness_mm * 0.6

    metal_volume_mm3 = (2 * pi * centerline_radius_mm) * cross_section_area_mm2 * shank_factor
    metal_volume_cm3 = metal_volume_mm3 / 1000.0
    density = METAL_DENSITY_G_PER_CM3[params.metal]
    return metal_volume_cm3 * density


def _estimate_center_stone_carat(params: RingParameters) -> float:
    return _estimate_stone_carat(
        diameter_mm=params.gemstone_size_mm,
        gemstone_type=params.gemstone_type,
        center_stone_shape=params.center_stone_shape,
    )


def _estimate_side_stones_carat(params: RingParameters) -> float:
    if params.side_stone_count <= 0:
        return 0.0
    side_diameter_mm = max(0.8, params.gemstone_size_mm * 0.34)
    per_stone = _estimate_stone_carat(
        diameter_mm=side_diameter_mm,
        gemstone_type=params.gemstone_type,
        center_stone_shape="round",
    )
    return per_stone * params.side_stone_count


def _estimate_stone_carat(diameter_mm: float, gemstone_type: str, center_stone_shape: str) -> float:
    depth_factor = {
        "round": 0.62,
        "oval": 0.58,
        "princess": 0.68,
        "emerald_cut": 0.54,
        "marquise": 0.52,
        "pear": 0.55,
    }.get(center_stone_shape, 0.6)
    shape_scale = {
        "round": 1.0,
        "oval": 1.12,
        "princess": 0.97,
        "emerald_cut": 1.08,
        "marquise": 1.18,
        "pear": 1.1,
    }.get(center_stone_shape, 1.0)

    radius_mm = diameter_mm / 2.0
    depth_mm = max(0.5, diameter_mm * depth_factor)
    volume_mm3 = (4.0 / 3.0) * pi * radius_mm * radius_mm * (depth_mm / 2.0) * shape_scale
    volume_cm3 = volume_mm3 / 1000.0
    stone_weight_g = volume_cm3 * GEMSTONE_DENSITY_G_PER_CM3[gemstone_type]
    # 1 carat = 0.2 grams
    return stone_weight_g / 0.2


pricing_service = PricingService()
