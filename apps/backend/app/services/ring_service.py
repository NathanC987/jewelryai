import logging
from time import perf_counter
from uuid import uuid4

from app.domain.benchmark import EditLatencyBenchmarkResponse, OperationLatencyMetrics
from app.domain.ring import (
    ComponentEdge,
    ComponentNode,
    CostEstimate,
    ManufacturabilityWarning,
    RingGraph,
    RingGraphResponse,
    RingParameters,
    RingStateResponse,
    RingUpdateDiff,
    RingUpdateRequest,
)
from app.services.pricing_service import pricing_service


class RingService:
    """In-memory ring graph service for single-user/local MVP mode."""

    def __init__(self) -> None:
        self._store: dict[str, RingGraph] = {}
        self._logger = logging.getLogger("service.ring")

    def create_ring(self, parameters: RingParameters | None = None) -> RingStateResponse:
        ring_id = str(uuid4())
        graph = RingGraph(
            ring_id=ring_id,
            parameters=parameters or RingParameters(),
            nodes=_build_default_nodes(),
            edges=_build_default_edges(),
        )
        self._store[ring_id] = graph
        return self._to_response(graph)

    def get_graph(self, ring_id: str) -> RingGraphResponse | None:
        graph = self._store.get(ring_id)
        if not graph:
            return None

        return RingGraphResponse(
            ring_id=graph.ring_id,
            version=graph.version,
            nodes=list(graph.nodes.values()),
            edges=graph.edges,
        )

    def get_ring(self, ring_id: str) -> RingStateResponse | None:
        graph = self._store.get(ring_id)
        if not graph:
            return None
        return self._to_response(graph)

    def update_ring(self, ring_id: str, update: RingUpdateRequest) -> RingStateResponse | None:
        graph = self._store.get(ring_id)
        if not graph:
            return None

        from_version = graph.version
        changed_fields: list[str] = []
        impacted_components: set[str] = set()

        if update.metal is not None:
            graph.parameters.metal = update.metal
            changed_fields.append("metal")
            impacted_components.update({"band", "prongs"})
        if update.gemstone_type is not None:
            graph.parameters.gemstone_type = update.gemstone_type
            changed_fields.append("gemstone_type")
            impacted_components.update({"center_stone", "side_stones", "prongs"})
        if update.center_stone_shape is not None:
            graph.parameters.center_stone_shape = update.center_stone_shape
            changed_fields.append("center_stone_shape")
            impacted_components.update({"center_stone", "prongs"})
        if update.prong_count is not None:
            graph.parameters.prong_count = update.prong_count
            changed_fields.append("prong_count")
            impacted_components.update({"prongs", "center_stone"})
        if update.band_profile is not None:
            graph.parameters.band_profile = update.band_profile
            changed_fields.append("band_profile")
            impacted_components.update({"band"})
        if update.side_stone_count is not None:
            graph.parameters.side_stone_count = update.side_stone_count
            changed_fields.append("side_stone_count")
            impacted_components.update({"side_stones", "band"})
        if update.setting_family is not None:
            graph.parameters.setting_family = update.setting_family
            changed_fields.append("setting_family")
            impacted_components.update({"center_stone", "prongs"})
        if update.setting_variant is not None:
            graph.parameters.setting_variant = update.setting_variant
            changed_fields.append("setting_variant")
            impacted_components.update({"center_stone", "prongs"})
        if update.setting_openheart is not None:
            graph.parameters.setting_openheart = update.setting_openheart
            changed_fields.append("setting_openheart")
            impacted_components.update({"center_stone", "prongs"})
        if update.shank_family is not None:
            graph.parameters.shank_family = update.shank_family
            changed_fields.append("shank_family")
            impacted_components.update({"band"})
        if update.shank_variant is not None:
            graph.parameters.shank_variant = update.shank_variant
            changed_fields.append("shank_variant")
            impacted_components.update({"band"})
        if update.setting_height_mm is not None:
            graph.parameters.setting_height_mm = update.setting_height_mm
            changed_fields.append("setting_height_mm")
            impacted_components.update({"prongs", "center_stone"})
        if update.gemstone_size_mm is not None:
            graph.parameters.gemstone_size_mm = update.gemstone_size_mm
            changed_fields.append("gemstone_size_mm")
            impacted_components.update({"center_stone", "prongs"})
        if update.band_thickness_mm is not None:
            graph.parameters.band_thickness_mm = update.band_thickness_mm
            changed_fields.append("band_thickness_mm")
            impacted_components.update({"band", "prongs"})

        if changed_fields:
            graph.version += 1

        update_diff = RingUpdateDiff(
            changed_fields=changed_fields,
            impacted_components=sorted(impacted_components),
            from_version=from_version,
            to_version=graph.version,
        )

        self._logger.info(
            {
                "ring_id": ring_id,
                "operation": "ring_update",
                "status": "success",
                "changed_fields": changed_fields,
                "impacted_components": sorted(impacted_components),
                "from_version": from_version,
                "to_version": graph.version,
            }
        )

        self._store[ring_id] = graph
        return self._to_response(graph, last_update_diff=update_diff)

    def benchmark_required_edits(
        self,
        iterations: int,
        target_max_ms: float,
    ) -> EditLatencyBenchmarkResponse:
        base_state = self.create_ring()
        ring_id = base_state.ring_id

        operation_samples: dict[str, list[float]] = {
            "material_swap": [],
            "gemstone_type_swap": [],
            "gemstone_size_adjustment": [],
            "band_thickness_adjustment": [],
        }

        metals = ["gold", "rose_gold", "platinum", "silver"]
        gemstones = ["diamond", "ruby", "emerald", "sapphire"]

        for i in range(iterations):
            edit_sequence = [
                (
                    "material_swap",
                    RingUpdateRequest(metal=metals[i % len(metals)]),
                ),
                (
                    "gemstone_type_swap",
                    RingUpdateRequest(gemstone_type=gemstones[i % len(gemstones)]),
                ),
                (
                    "gemstone_size_adjustment",
                    RingUpdateRequest(gemstone_size_mm=1.0 + ((i * 1.3) % 11.0)),
                ),
                (
                    "band_thickness_adjustment",
                    RingUpdateRequest(band_thickness_mm=1.2 + ((i * 0.37) % 3.8)),
                ),
            ]

            for operation, request in edit_sequence:
                started = perf_counter()
                self.update_ring(ring_id, request)
                elapsed_ms = (perf_counter() - started) * 1000.0
                operation_samples[operation].append(round(elapsed_ms, 3))

        per_operation: list[OperationLatencyMetrics] = []
        overall_max_ms = 0.0
        for operation, samples in operation_samples.items():
            op_min = min(samples)
            op_max = max(samples)
            op_avg = sum(samples) / len(samples)
            overall_max_ms = max(overall_max_ms, op_max)
            per_operation.append(
                OperationLatencyMetrics(
                    operation=operation,
                    samples=len(samples),
                    min_ms=round(op_min, 3),
                    avg_ms=round(op_avg, 3),
                    max_ms=round(op_max, 3),
                )
            )

        meets_target = overall_max_ms <= target_max_ms
        self._logger.info(
            {
                "operation": "benchmark_required_edits",
                "ring_id": ring_id,
                "iterations": iterations,
                "target_max_ms": target_max_ms,
                "overall_max_ms": round(overall_max_ms, 3),
                "meets_target": meets_target,
            }
        )

        return EditLatencyBenchmarkResponse(
            ring_id=ring_id,
            iterations=iterations,
            target_max_ms=target_max_ms,
            meets_target=meets_target,
            overall_max_ms=round(overall_max_ms, 3),
            per_operation=per_operation,
        )

    def _to_response(
        self,
        graph: RingGraph,
        last_update_diff: RingUpdateDiff | None = None,
    ) -> RingStateResponse:
        params = graph.parameters
        cost_estimate = pricing_service.estimate_cost(params)

        warnings: list[ManufacturabilityWarning] = []
        if params.band_thickness_mm < 1.6:
            warnings.append(
                ManufacturabilityWarning(
                    code="BAND_THIN",
                    message="Band thickness may be too thin for reliable casting.",
                )
            )
        if params.gemstone_size_mm > 10.0:
            warnings.append(
                ManufacturabilityWarning(
                    code="STONE_STABILITY",
                    message="Large center stone may require stronger prong settings.",
                )
            )
        if params.setting_family == "bezel" and params.setting_openheart:
            warnings.append(
                ManufacturabilityWarning(
                    code="OPENHEART_COMPLEXITY",
                    message="Open-heart bezel requires tighter tolerance checks for production.",
                )
            )

        return RingStateResponse(
            ring_id=graph.ring_id,
            parameters=params,
            graph_version=graph.version,
            cost_estimate=CostEstimate(**cost_estimate.model_dump()),
            manufacturability_warnings=warnings,
            last_update_diff=last_update_diff,
            glb_asset_uri=f"/artifacts/{graph.ring_id}/model.glb",
        )


def _build_default_nodes() -> dict[str, ComponentNode]:
    return {
        "ring": ComponentNode(node_id="ring", component_type="ring"),
        "band": ComponentNode(node_id="band", component_type="band"),
        "center_stone": ComponentNode(
            node_id="center_stone", component_type="center_stone"
        ),
        "side_stones": ComponentNode(node_id="side_stones", component_type="side_stones"),
        "prongs": ComponentNode(node_id="prongs", component_type="prongs"),
    }


def _build_default_edges() -> list[ComponentEdge]:
    return [
        ComponentEdge(source_node_id="ring", target_node_id="band", relation="contains"),
        ComponentEdge(
            source_node_id="ring", target_node_id="center_stone", relation="contains"
        ),
        ComponentEdge(
            source_node_id="ring", target_node_id="side_stones", relation="contains"
        ),
        ComponentEdge(source_node_id="ring", target_node_id="prongs", relation="contains"),
        ComponentEdge(
            source_node_id="prongs", target_node_id="center_stone", relation="supports"
        ),
    ]
ring_service = RingService()
