from typing import Literal

from pydantic import BaseModel, Field

Metal = Literal["gold", "rose_gold", "platinum", "silver"]
Gemstone = Literal["diamond", "ruby", "emerald", "sapphire"]
CenterStoneShape = Literal["round", "oval", "princess", "emerald_cut", "marquise", "pear"]
BandProfile = Literal["classic", "flat", "knife_edge", "tapered"]
SettingFamily = Literal["basket", "peghead", "bezel", "halo", "cluster"]
ShankFamily = Literal["classic", "cathedral", "advanced"]
TemplateId = Literal[
    "solitaire_ring",
    "halo_ring",
    "pave_band_ring",
    "split_shank_ring",
    "three_stone_ring",
]
StyleTag = Literal["modern", "vintage", "royal", "minimalist"]


class RingParameters(BaseModel):
    template_id: TemplateId = "solitaire_ring"
    style_tag: StyleTag = "modern"
    metal: Metal = "gold"
    gemstone_type: Gemstone = "diamond"
    center_stone_shape: CenterStoneShape = "round"
    prong_count: int = Field(default=4, ge=2, le=8)
    band_profile: BandProfile = "classic"
    side_stone_count: int = Field(default=0, ge=0, le=24)
    setting_family: SettingFamily = "peghead"
    setting_variant: int = Field(default=4, ge=1, le=20)
    setting_openheart: bool = False
    shank_family: ShankFamily = "classic"
    shank_variant: int = Field(default=1, ge=1, le=20)
    setting_height_mm: float = Field(default=1.8, ge=0.6, le=5.0)
    gemstone_size_mm: float = Field(default=4.0, ge=1.0, le=12.0)
    band_thickness_mm: float = Field(default=2.0, ge=1.2, le=5.0)


class RingGraph(BaseModel):
    ring_id: str
    parameters: RingParameters
    version: int = 1
    nodes: dict[str, "ComponentNode"] = Field(default_factory=dict)
    edges: list["ComponentEdge"] = Field(default_factory=list)
    components: dict[str, str] = Field(
        default_factory=lambda: {
            "band": "active",
            "center_stone": "active",
            "side_stones": "active",
            "prongs": "active",
        }
    )


class ComponentNode(BaseModel):
    node_id: str
    component_type: Literal["ring", "band", "center_stone", "side_stones", "prongs"]
    state: Literal["active"] = "active"


class ComponentEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    relation: Literal["contains", "supports"]


class RingUpdateRequest(BaseModel):
    metal: Metal | None = None
    gemstone_type: Gemstone | None = None
    center_stone_shape: CenterStoneShape | None = None
    prong_count: int | None = Field(default=None, ge=2, le=8)
    band_profile: BandProfile | None = None
    side_stone_count: int | None = Field(default=None, ge=0, le=24)
    setting_family: SettingFamily | None = None
    setting_variant: int | None = Field(default=None, ge=1, le=20)
    setting_openheart: bool | None = None
    shank_family: ShankFamily | None = None
    shank_variant: int | None = Field(default=None, ge=1, le=20)
    setting_height_mm: float | None = Field(default=None, ge=0.6, le=5.0)
    gemstone_size_mm: float | None = Field(default=None, ge=1.0, le=12.0)
    band_thickness_mm: float | None = Field(default=None, ge=1.2, le=5.0)


class RingUpdateDiff(BaseModel):
    changed_fields: list[str]
    impacted_components: list[str]
    from_version: int
    to_version: int


class CostEstimate(BaseModel):
    metal_weight_g: float
    gemstone_carat: float
    estimated_price_usd: float


class ManufacturabilityWarning(BaseModel):
    code: str
    message: str


class RingStateResponse(BaseModel):
    ring_id: str
    parameters: RingParameters
    graph_version: int
    cost_estimate: CostEstimate
    manufacturability_warnings: list[ManufacturabilityWarning]
    last_update_diff: RingUpdateDiff | None = None
    glb_asset_uri: str


class RingVariationSuggestionResponse(BaseModel):
    style_name: str
    summary: str
    ring: RingStateResponse


class RingVariationSetResponse(BaseModel):
    source_ring_id: str
    suggestions: list[RingVariationSuggestionResponse]


class RingGraphResponse(BaseModel):
    ring_id: str
    version: int
    nodes: list[ComponentNode]
    edges: list[ComponentEdge]


class PromptRingGenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=500)


class RingChangePromptRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=300)


class PromptInterpretationResponse(BaseModel):
    normalized_prompt: str
    template_id: TemplateId
    style_tag: StyleTag
    selected_components: list[str]
    confidence: float
    notes: str


class PromptRingGenerateResponse(BaseModel):
    interpretation: PromptInterpretationResponse
    ring: RingStateResponse
