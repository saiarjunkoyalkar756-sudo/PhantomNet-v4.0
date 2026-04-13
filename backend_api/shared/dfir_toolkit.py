# backend_api/dfir_toolkit.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import random
import time
import uuid


# --- Data Models for DFIR Operations ---
class ForensicResult(BaseModel):
    operation_id: str = Field(..., description="Unique ID for the DFIR operation")
    tool: str = Field(
        ..., description="DFIR tool used (e.g., Volatility, Autopsy, YARA)"
    )
    target: str = Field(
        ...,
        description="Target of the operation (e.g., memory dump, disk image, file hash)",
    )
    findings: List[Dict[str, Any]] = Field(
        [], description="List of findings from the operation"
    )
    summary: Optional[str] = Field(
        None, description="Summary of the DFIR operation results"
    )
    status: str = Field(
        "completed", description="Status of the operation (e.g., 'completed', 'failed')"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Timestamp of the operation"
    )


class MemoryDumpAnalysisRequest(BaseModel):
    dump_path: str = Field(..., description="Path to the memory dump file")
    profile: str = Field("Win10x64_19041", description="Volatility profile to use")
    plugins: List[str] = Field(
        ["pslist", "netscan", "malfind"], description="Volatility plugins to run"
    )


class DiskForensicsRequest(BaseModel):
    image_path: str = Field(..., description="Path to the disk image file")
    filesystem_type: str = Field("NTFS", description="Filesystem type of the image")
    keywords: List[str] = Field([], description="Keywords to search for")


class LogTimeliningRequest(BaseModel):
    log_paths: List[str] = Field(..., description="Paths to log files")
    sort_by: str = Field("timestamp", description="Field to sort timeline by")
    filter_keywords: List[str] = Field([], description="Keywords to filter log entries")


class MalwareSandboxRequest(BaseModel):
    file_path: str = Field(..., description="Path to the malware sample file")
    analysis_duration: int = Field(
        60, ge=10, le=300, description="Duration of sandbox analysis in seconds"
    )
    network_access: bool = Field(
        True, description="Allow network access during sandboxing"
    )


class YARAScanRequest(BaseModel):
    scan_paths: List[str] = Field(..., description="Paths to scan for malware")
    rule_paths: List[str] = Field(..., description="Paths to YARA rule files")


class DFIRToolkit:
    def __init__(self):
        self.operations: Dict[str, ForensicResult] = (
            {}
        )  # Store ongoing/completed operations

    async def analyze_memory_dump(
        self, request: MemoryDumpAnalysisRequest
    ) -> ForensicResult:
        """Simulates memory dump analysis using Volatility."""
        operation_id = str(uuid.uuid4())
        logger.info(
            f"[{__name__}] Simulating Volatility analysis for {request.dump_path}"
        )
        self.operations[operation_id] = ForensicResult(
            operation_id=operation_id,
            tool="Volatility",
            target=request.dump_path,
            summary="Volatility analysis started...",
            status="running",
        )
        await asyncio.sleep(random.uniform(5, 15))  # Simulate analysis time

        findings = (
            [
                {
                    "type": "process",
                    "details": f"Suspicious process found (PID {random.randint(100, 999)})",
                },
                {
                    "type": "network_connection",
                    "details": f"Outbound connection to {random.choice(['malicious.com', 'bad.ru'])}",
                },
            ]
            if random.random() < 0.7
            else []
        )

        summary = f"Completed Volatility analysis on {request.dump_path}. Found {len(findings)} findings."
        self.operations[operation_id].findings = findings
        self.operations[operation_id].summary = summary
        self.operations[operation_id].status = "completed"
        return self.operations[operation_id]

    async def perform_disk_forensics(
        self, request: DiskForensicsRequest
    ) -> ForensicResult:
        """Simulates disk forensics using Autopsy/Sleuthkit."""
        operation_id = str(uuid.uuid4())
        logger.info(f"[{__name__}] Simulating disk forensics for {request.image_path}")
        self.operations[operation_id] = ForensicResult(
            operation_id=operation_id,
            tool="Autopsy/Sleuthkit",
            target=request.image_path,
            summary="Disk forensics operation started...",
            status="running",
        )
        await asyncio.sleep(random.uniform(10, 25))  # Simulate analysis time

        findings = []
        if request.keywords:
            if random.random() < 0.6:
                findings.append(
                    {
                        "type": "keyword_hit",
                        "details": f"Found '{random.choice(request.keywords)}' in deleted files.",
                    }
                )
        if random.random() < 0.4:
            findings.append(
                {"type": "malicious_file", "details": "Suspicious executable detected."}
            )

        summary = f"Completed disk forensics on {request.image_path}. Found {len(findings)} findings."
        self.operations[operation_id].findings = findings
        self.operations[operation_id].summary = summary
        self.operations[operation_id].status = "completed"
        return self.operations[operation_id]

    async def create_log_timeline(
        self, request: LogTimeliningRequest
    ) -> ForensicResult:
        """Simulates creating a log timeline."""
        operation_id = str(uuid.uuid4())
        logger.info(
            f"[{__name__}] Simulating log timelining for {len(request.log_paths)} log files."
        )
        self.operations[operation_id] = ForensicResult(
            operation_id=operation_id,
            tool="Log2Timeline",
            target=f"{len(request.log_paths)} log files",
            summary="Log timelining started...",
            status="running",
        )
        await asyncio.sleep(random.uniform(3, 8))  # Simulate analysis time

        findings = []
        if random.random() < 0.5:
            findings.append(
                {
                    "type": "time_drift",
                    "details": "Significant time drift detected in some log entries.",
                }
            )
        if request.filter_keywords:
            if random.random() < 0.7:
                findings.append(
                    {
                        "type": "relevant_entry",
                        "details": f"Log entry matching '{random.choice(request.filter_keywords)}' at {datetime.now().isoformat()}",
                    }
                )

        summary = f"Completed log timelining. Found {len(findings)} findings."
        self.operations[operation_id].findings = findings
        self.operations[operation_id].summary = summary
        self.operations[operation_id].status = "completed"
        return self.operations[operation_id]

    async def sandbox_malware(self, request: MalwareSandboxRequest) -> ForensicResult:
        """Simulates malware sandboxing."""
        operation_id = str(uuid.uuid4())
        logger.info(
            f"[{__name__}] Simulating malware sandboxing for {request.file_path}"
        )
        self.operations[operation_id] = ForensicResult(
            operation_id=operation_id,
            tool="Cuckoo Sandbox",
            target=request.file_path,
            summary="Malware sandboxing started...",
            status="running",
        )
        await asyncio.sleep(request.analysis_duration / 5)  # Simulate quicker for demo

        findings = (
            [
                {
                    "type": "network_activity",
                    "details": "Connected to C2 server 1.2.3.4",
                },
                {
                    "type": "filesystem_changes",
                    "details": "Dropped persistence mechanism in user startup folder",
                },
            ]
            if random.random() < 0.8
            else []
        )

        summary = f"Completed malware sandboxing for {request.file_path}. Behavior analysis shows {len(findings)} malicious indicators."
        self.operations[operation_id].findings = findings
        self.operations[operation_id].summary = summary
        self.operations[operation_id].status = "completed"
        return self.operations[operation_id]

    async def run_yara_scan(self, request: YARAScanRequest) -> ForensicResult:
        """Simulates running a YARA scan."""
        operation_id = str(uuid.uuid4())
        logger.info(
            f"[{__name__}] Simulating YARA scan over {len(request.scan_paths)} paths."
        )
        self.operations[operation_id] = ForensicResult(
            operation_id=operation_id,
            tool="YARA",
            target=f"{len(request.scan_paths)} paths",
            summary="YARA scan started...",
            status="running",
        )
        await asyncio.sleep(random.uniform(2, 7))  # Simulate scan time

        findings = []
        if random.random() < 0.6:
            findings.append(
                {
                    "type": "yara_match",
                    "details": f"Rule '{random.choice(['APT28_Beacon', 'Ransomware_Crypter'])}' matched in {random.choice(request.scan_paths)}",
                }
            )

        summary = f"Completed YARA scan. Found {len(findings)} matches."
        self.operations[operation_id].findings = findings
        self.operations[operation_id].summary = summary
        self.operations[operation_id].status = "completed"
        return self.operations[operation_id]

    def get_operation_status(self, operation_id: str) -> Optional[ForensicResult]:
        """Retrieves the status of a specific DFIR operation."""
        return self.operations.get(operation_id)


if __name__ == "__main__":
    dfir_toolkit = DFIRToolkit()

    async def test_dfir():
        print("--- Testing Memory Dump Analysis ---")
        mem_request = MemoryDumpAnalysisRequest(dump_path="/forensics/memdump.raw")
        mem_result = await dfir_toolkit.analyze_memory_dump(mem_request)
        print(json.dumps(mem_result.dict(), indent=2))

        print("\n--- Testing Disk Forensics ---")
        disk_request = DiskForensicsRequest(
            image_path="/forensics/disk.img", keywords=["confidential", "passwords"]
        )
        disk_result = await dfir_toolkit.perform_disk_forensics(disk_request)
        print(json.dumps(disk_result.dict(), indent=2))

        print("\n--- Testing Malware Sandboxing ---")
        malware_request = MalwareSandboxRequest(
            file_path="/samples/malware.exe", analysis_duration=30
        )
        malware_result = await dfir_toolkit.sandbox_malware(malware_request)
        print(json.dumps(malware_result.dict(), indent=2))

        print("\n--- Testing YARA Scan ---")
        yara_request = YARAScanRequest(
            scan_paths=["/var/www/html", "/usr/bin"], rule_paths=["/etc/yara/rules.yar"]
        )
        yara_result = await dfir_toolkit.run_yara_scan(yara_request)
        print(json.dumps(yara_result.dict(), indent=2))

        print("\n--- Getting Operation Status (Memory Dump) ---")
        status_result = dfir_toolkit.get_operation_status(mem_result.operation_id)
        print(json.dumps(status_result.dict(), indent=2))

    asyncio.run(test_dfir())
