from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectSummary(BaseModel):
    project_id: str = Field(description="Local project identifier")
    name: str
    mode: str = Field(default="single-user-local")


@router.get("", response_model=list[ProjectSummary])
def list_projects() -> list[ProjectSummary]:
    # Placeholder static response until persistence layer is connected.
    return [ProjectSummary(project_id="demo", name="Local Demo Project")]
