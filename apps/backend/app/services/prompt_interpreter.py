from app.domain.ring import (
    PromptInterpretationResponse,
    RingParameters,
    RingUpdateRequest,
    SettingFamily,
    ShankFamily,
    TemplateId,
    StyleTag,
)
from app.services.component_library import AssemblyContext, open_component_library


class PromptInterpreterService:
    """Deterministic prompt interpreter for prompt-first immediate release."""

    def interpret(self, prompt: str) -> tuple[PromptInterpretationResponse, RingParameters]:
        normalized = " ".join(prompt.strip().lower().split())

        template_id = self._infer_template(normalized)
        style_tag = self._infer_style(normalized)
        metal = self._infer_metal(normalized)
        gemstone_type = self._infer_gemstone(normalized)
        center_shape = self._infer_shape(normalized)
        setting_family = self._infer_setting_family(normalized)
        setting_variant = self._infer_setting_variant(normalized)
        setting_openheart = self._infer_openheart(normalized)
        shank_family = self._infer_shank_family(normalized, template_id)
        shank_variant = self._infer_shank_variant(normalized)

        parameters = self._template_defaults(template_id)
        parameters.style_tag = style_tag
        parameters.metal = metal
        parameters.gemstone_type = gemstone_type
        parameters.center_stone_shape = center_shape
        parameters.setting_family = setting_family
        parameters.setting_variant = setting_variant
        parameters.setting_openheart = setting_openheart
        parameters.shank_family = shank_family
        parameters.shank_variant = shank_variant

        # Style remaps adjust proportions while keeping template topology stable.
        self._apply_style_remap(parameters, style_tag)

        selected_components = open_component_library.selected_components(
            AssemblyContext(
                template_id=parameters.template_id,
                style_tag=parameters.style_tag,
                band_profile=parameters.band_profile,
                band_thickness_mm=parameters.band_thickness_mm,
                gemstone_size_mm=parameters.gemstone_size_mm,
                gemstone_type=parameters.gemstone_type,
                center_stone_shape=parameters.center_stone_shape,
                prong_count=parameters.prong_count,
                side_stone_count=parameters.side_stone_count,
                setting_family=parameters.setting_family,
                setting_variant=parameters.setting_variant,
                setting_openheart=parameters.setting_openheart,
                shank_family=parameters.shank_family,
                shank_variant=parameters.shank_variant,
                setting_height_mm=parameters.setting_height_mm,
            )
        )

        confidence = self._confidence_for(normalized)
        interpretation = PromptInterpretationResponse(
            normalized_prompt=normalized,
            template_id=template_id,
            style_tag=style_tag,
            selected_components=selected_components,
            confidence=confidence,
            notes="Deterministic prompt interpreter selected template and parameters.",
        )
        return interpretation, parameters

    def interpret_change_prompt(self, prompt: str, current: RingParameters) -> RingUpdateRequest:
        normalized = " ".join(prompt.strip().lower().split())
        update = RingUpdateRequest()

        if any(token in normalized for token in ("round", "oval", "princess", "emerald cut", "emerald-cut", "marquise", "pear", "teardrop")):
            update.center_stone_shape = self._infer_shape(normalized)

        if any(token in normalized for token in ("gold", "rose gold", "platinum", "silver")):
            update.metal = self._infer_metal(normalized)

        if any(token in normalized for token in ("diamond", "ruby", "emerald", "sapphire")):
            update.gemstone_type = self._infer_gemstone(normalized)

        if any(token in normalized for token in ("basket", "peghead", "bezel", "halo", "cluster")):
            update.setting_family = self._infer_setting_family(normalized)

        if any(token in normalized for token in ("open heart", "openheart")):
            update.setting_openheart = True
        elif "without open heart" in normalized or "no open heart" in normalized:
            update.setting_openheart = False

        if any(token in normalized for token in ("classic shank", "cathedral", "advanced shank", "classic band", "cathedral shank")):
            update.shank_family = self._infer_shank_family(normalized, current.template_id)

        setting_variant = self._extract_explicit_number(normalized, ("setting", "basket", "peghead", "bezel", "halo", "cluster"))
        if setting_variant is not None:
            update.setting_variant = setting_variant

        shank_variant = self._extract_explicit_number(normalized, ("shank", "band", "cathedral", "advanced", "classic"))
        if shank_variant is not None:
            update.shank_variant = shank_variant

        prong_count = self._extract_explicit_number(normalized, ("prong", "claw"))
        if prong_count is not None:
            update.prong_count = max(2, min(8, prong_count))

        size_mm = self._extract_mm_value(normalized)
        if size_mm is not None:
            update.gemstone_size_mm = size_mm

        return update

    def _infer_template(self, normalized: str) -> TemplateId:
        if "solitaire" in normalized:
            return "solitaire_ring"
        if "three stone" in normalized or "trilogy" in normalized:
            return "three_stone_ring"
        if "split shank" in normalized:
            return "split_shank_ring"
        if "pave" in normalized or "micro pave" in normalized:
            return "pave_band_ring"
        if "halo" in normalized:
            return "halo_ring"
        # Prefer the hero-quality single-ring path when template is ambiguous.
        return "solitaire_ring"

    def _infer_style(self, normalized: str) -> StyleTag:
        if "vintage" in normalized or "antique" in normalized:
            return "vintage"
        if "royal" in normalized or "luxury" in normalized or "ornate" in normalized:
            return "royal"
        if "minimal" in normalized or "clean" in normalized or "simple" in normalized:
            return "minimalist"
        return "modern"

    def _infer_metal(self, normalized: str):
        if "rose gold" in normalized:
            return "rose_gold"
        if "platinum" in normalized:
            return "platinum"
        if "silver" in normalized:
            return "silver"
        return "gold"

    def _infer_gemstone(self, normalized: str):
        if "ruby" in normalized:
            return "ruby"
        if "emerald" in normalized:
            return "emerald"
        if "sapphire" in normalized:
            return "sapphire"
        return "diamond"

    def _infer_shape(self, normalized: str):
        if "oval" in normalized:
            return "oval"
        if "princess" in normalized or "square" in normalized:
            return "princess"
        if "emerald cut" in normalized or "emerald-cut" in normalized:
            return "emerald_cut"
        if "marquise" in normalized:
            return "marquise"
        if "pear" in normalized or "teardrop" in normalized:
            return "pear"
        return "round"

    def _infer_setting_family(self, normalized: str) -> SettingFamily:
        if "cluster" in normalized:
            return "cluster"
        if "halo" in normalized:
            return "halo"
        if "bezel" in normalized:
            return "bezel"
        if "basket" in normalized:
            return "basket"
        return "peghead"

    def _infer_shank_family(self, normalized: str, template_id: TemplateId) -> ShankFamily:
        if "advanced" in normalized:
            return "advanced"
        if "cathedral" in normalized:
            return "cathedral"
        if template_id in {"halo_ring", "three_stone_ring"}:
            return "cathedral"
        return "classic"

    def _infer_setting_variant(self, normalized: str) -> int:
        picked = self._extract_explicit_number(normalized, ("basket", "peghead", "bezel", "halo", "cluster", "setting"))
        return picked or 4

    def _infer_shank_variant(self, normalized: str) -> int:
        picked = self._extract_explicit_number(normalized, ("classic", "cathedral", "advanced", "shank", "band"))
        return picked or 1

    def _infer_openheart(self, normalized: str) -> bool:
        if "without open heart" in normalized or "no open heart" in normalized:
            return False
        return "open heart" in normalized or "openheart" in normalized

    def _template_defaults(self, template_id: TemplateId) -> RingParameters:
        if template_id == "halo_ring":
            return RingParameters(
                template_id=template_id,
                prong_count=6,
                side_stone_count=14,
                gemstone_size_mm=5.2,
                setting_height_mm=2.2,
                band_thickness_mm=2.0,
                band_profile="classic",
            )
        if template_id == "pave_band_ring":
            return RingParameters(
                template_id=template_id,
                prong_count=4,
                side_stone_count=18,
                gemstone_size_mm=4.4,
                setting_height_mm=1.7,
                band_thickness_mm=1.9,
                band_profile="flat",
            )
        if template_id == "split_shank_ring":
            return RingParameters(
                template_id=template_id,
                prong_count=6,
                side_stone_count=8,
                gemstone_size_mm=5.6,
                setting_height_mm=2.4,
                band_thickness_mm=2.3,
                band_profile="knife_edge",
            )
        if template_id == "three_stone_ring":
            return RingParameters(
                template_id=template_id,
                prong_count=4,
                side_stone_count=2,
                gemstone_size_mm=5.0,
                setting_height_mm=2.0,
                band_thickness_mm=2.2,
                band_profile="classic",
            )

        return RingParameters(
            template_id="solitaire_ring",
            prong_count=4,
            side_stone_count=0,
            gemstone_size_mm=4.6,
            setting_height_mm=1.9,
            band_thickness_mm=2.0,
            band_profile="tapered",
        )

    def _apply_style_remap(self, parameters: RingParameters, style_tag: StyleTag) -> None:
        if style_tag == "minimalist":
            parameters.band_profile = "flat"
            parameters.prong_count = min(parameters.prong_count, 4)
            parameters.setting_height_mm = max(0.9, parameters.setting_height_mm - 0.35)
            parameters.gemstone_size_mm = max(3.6, parameters.gemstone_size_mm - 0.4)
            if parameters.setting_family in {"cluster", "halo"}:
                parameters.setting_family = "peghead"
            return

        if style_tag == "vintage":
            parameters.band_profile = "classic"
            parameters.prong_count = max(parameters.prong_count, 6)
            parameters.setting_height_mm = min(5.0, parameters.setting_height_mm + 0.25)
            parameters.side_stone_count = max(parameters.side_stone_count, 10)
            return

        if style_tag == "royal":
            parameters.band_profile = "tapered"
            parameters.prong_count = max(parameters.prong_count, 6)
            parameters.setting_height_mm = min(5.0, parameters.setting_height_mm + 0.3)
            parameters.gemstone_size_mm = min(12.0, parameters.gemstone_size_mm + 0.45)
            parameters.shank_family = "cathedral"

            # Keep royal solitaire clean; richer side-stone layouts are reserved for non-solitaire templates.
            if parameters.template_id == "solitaire_ring":
                parameters.side_stone_count = 0
            else:
                parameters.side_stone_count = max(parameters.side_stone_count, 10)
            return

        # modern
        parameters.band_profile = "knife_edge" if parameters.template_id == "split_shank_ring" else parameters.band_profile

    def _extract_explicit_number(self, normalized: str, anchors: tuple[str, ...]) -> int | None:
        tokens = normalized.replace("-", " ").split()
        for index, token in enumerate(tokens):
            if not token.isdigit():
                continue
            number = int(token)
            window = " ".join(tokens[max(0, index - 2): min(len(tokens), index + 3)])
            if any(anchor in window for anchor in anchors):
                return number
        return None

    def _extract_mm_value(self, normalized: str) -> float | None:
        tokens = normalized.replace("mm", " mm ").replace("-", " ").split()
        for index, token in enumerate(tokens):
            try:
                value = float(token)
            except ValueError:
                continue
            tail = " ".join(tokens[index: min(len(tokens), index + 3)])
            if "mm" in tail or "millimeter" in tail or "size" in tail:
                return max(1.0, min(12.0, value))
        return None

    def _confidence_for(self, normalized: str) -> float:
        keyword_count = sum(
            1
            for token in (
                "halo",
                "solitaire",
                "pave",
                "split shank",
                "three stone",
                "vintage",
                "modern",
                "minimal",
                "royal",
                "oval",
                "princess",
                "emerald cut",
                "marquise",
                "pear",
                "gold",
                "platinum",
                "silver",
                "rose gold",
                "diamond",
                "ruby",
                "emerald",
                "sapphire",
            )
            if token in normalized
        )
        return round(min(0.98, 0.58 + keyword_count * 0.03), 3)


prompt_interpreter_service = PromptInterpreterService()
