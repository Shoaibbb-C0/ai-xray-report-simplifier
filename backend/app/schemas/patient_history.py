"""Stage 6 persistence boundary; no patient upload endpoint is enabled."""
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from ml.explanation.schema import BodyPartId, ExplanationResult


class ScanRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    user_id: UUID
    scan_date: date
    body_part: BodyPartId = BodyPartId.UNKNOWN
    body_side: Literal["left", "right", "unknown"] | None = None
    source_filename: str | None = Field(default=None, max_length=255)
    storage_path: str | None = None
    mime_type: Literal["image/png", "image/jpeg"] | None = None
    status: Literal["pending", "complete", "failed"] = "pending"

    @model_validator(mode="after")
    def owned_path(self):
        if self.storage_path is not None:
            prefix = f"{self.user_id}/{self.id}/"
            if not self.storage_path.startswith(prefix) or ".." in self.storage_path.split("/") or "\\" in self.storage_path or len(self.storage_path.split("/")) != 3 or not self.storage_path.split("/")[-1]:
                raise ValueError("Storage path must identify the owner, scan and file")
        return self


class AnalysisRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scan_id: UUID
    user_id: UUID
    xray_validation_result: Literal["x_ray", "non_xray", "uncertain"] | None = None
    xray_validation_confidence: float | None = Field(default=None, ge=0, le=1)
    body_part_result: BodyPartId | None = None
    body_part_confidence: float | None = Field(default=None, ge=0, le=1)
    fracture_result: Literal["fracture", "no_fracture", "uncertain", "not_analyzed"] | None = None
    fracture_confidence: float | None = Field(default=None, ge=0, le=1)
    explanation: ExplanationResult

    def persistence_payload(self) -> dict:
        """Preserve canonical explanation JSON, stripping ephemeral attention media.

        Callers must provide authenticated ownership, never trust request user IDs.
        No image is persisted here; Stage 7 must upload privately before storing paths.
        """
        payload = self.model_dump(mode="json")
        explanation = payload["explanation"]
        explanation["attention"]["overlay_base64"] = None
        explanation["attention"]["overlay_path"] = None
        explanation["attention"]["available"] = False
        payload["analysis_status"] = explanation["analysis_status"]
        payload["model_versions"] = explanation["model_versions"]
        return payload
