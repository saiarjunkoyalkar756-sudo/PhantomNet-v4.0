from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime
import uuid

router = APIRouter()

class CollectedArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the collected artifact.")
    name: str = Field(..., example="mft.dat", description="Name of the collected artifact.")
    type: str = Field(..., example="file", description="Type of artifact (e.g., 'file', 'memory_dump', 'registry_hive').")
    source_path: str = Field(..., example="/windows/system32/config/mft.dat", description="Original path of the artifact on the target system.")
    collection_time: datetime.datetime = Field(default_factory=datetime.datetime.now, description="Timestamp of when the artifact was collected.")
    storage_path: Optional[str] = Field(None, example="/forensics_repo/job_uuid/mft.dat", description="Path where the artifact is stored in the forensics repository.")
    size_bytes: Optional[int] = Field(None, example=102400)
    hash_md5: Optional[str] = Field(None, example="d41d8cd98f00b204e9800998ecf8427e")
    hash_sha256: Optional[str] = Field(None, example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the artifact.")

class EvidenceCollectionRequest(BaseModel):
    asset_id: str = Field(..., example="compromised-server-01", description="Identifier of the asset from which to collect evidence.")
    job_id: str = Field(..., description="ID of the forensic job this collection is part of.")
    artifact_types: List[str] = Field(..., example=["memory_dump", "system_logs", "user_files"], description="List of artifact types to collect.")
    collection_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for collection (e.g., specific file paths, memory regions).")

class EvidenceCollectionResponse(BaseModel):
    job_id: str = Field(..., description="ID of the associated forensic job.")
    asset_id: str = Field(..., example="compromised-server-01")
    collected_artifacts: List[CollectedArtifact] = Field(default_factory=list)
    status: str = Field(..., example="completed")
    message: str = Field(..., example="Evidence collection initiated successfully.")

@router.post("/collect/", response_model=EvidenceCollectionResponse)
async def collect_evidence(request: EvidenceCollectionRequest):
    """
    Simulates the collection of forensic evidence from a target asset.
    In a real system, this would trigger agent-side actions to collect data.
    """
    collected_artifacts = []
    
    for artifact_type in request.artifact_types:
        if artifact_type == "memory_dump":
            collected_artifacts.append(CollectedArtifact(
                name="memory.dmp",
                type="memory_dump",
                source_path="RAM",
                storage_path=f"/forensics_repo/{request.job_id}/memory.dmp",
                size_bytes=1024 * 1024 * 4096, # 4GB
                metadata={"tool": "Volatility3"}
            ))
        elif artifact_type == "system_logs":
            collected_artifacts.append(CollectedArtifact(
                name="syslog.zip",
                type="archive",
                source_path="/var/log/",
                storage_path=f"/forensics_repo/{request.job_id}/syslog.zip",
                size_bytes=52428800, # 50MB
                metadata={"log_source": "syslog", "compressed": True}
            ))
        elif artifact_type == "user_files":
            collected_artifacts.append(CollectedArtifact(
                name="user_documents.zip",
                type="archive",
                source_path="/home/user/",
                storage_path=f"/forensics_repo/{request.job_id}/user_documents.zip",
                size_bytes=20971520, # 20MB
                metadata={"user_id": "victim_user"}
            ))
        elif artifact_type == "registry_hives":
            collected_artifacts.append(CollectedArtifact(
                name="system_hives.zip",
                type="archive",
                source_path="C:\\Windows\\System32\\config",
                storage_path=f"/forensics_repo/{request.job_id}/registry_hives.zip",
                size_bytes=5242880, # 5MB
                metadata={"os": "Windows"}
            ))
        else:
            print(f"Warning: Unknown artifact type requested: {artifact_type}")

    return EvidenceCollectionResponse(
        job_id=request.job_id,
        asset_id=request.asset_id,
        collected_artifacts=collected_artifacts,
        status="completed",
        message=f"Simulated collection for {len(collected_artifacts)} artifacts completed for job {request.job_id} on asset {request.asset_id}."
    )