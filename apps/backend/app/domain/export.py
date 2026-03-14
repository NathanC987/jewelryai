from typing import Literal

from pydantic import BaseModel

ExportFormat = Literal["glb", "stl"]


class ExportResponse(BaseModel):
    ring_id: str
    format: ExportFormat
    artifact_uri: str
    status: Literal["ready"] = "ready"
