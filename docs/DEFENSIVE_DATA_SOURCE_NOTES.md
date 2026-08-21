# Defensive Data Source Notes

## Purpose

This note records external sources considered while designing PhantomNet's defensive-data registry. It is not a dataset import manifest and does not authorize download, ingestion, training, or use of any source. The implemented registry requires a source fingerprint, sanitization attestation, and, for external/public, uploaded, or tenant-sanitized sources, a recorded operator approval and license review.

## Candidate sources

| Source | Verified characteristics | PhantomNet handling |
|---|---|---|
| CSE-CIC-IDS2018 | The Canadian Institute for Cybersecurity describes seven attack scenarios and network/system logs with flow features. Its own documentation cautions that intrusion datasets require testing, tuning, and have limitations for real-world use. [1] | Treat only as an operator-reviewed external-public candidate. Do not auto-download; do not ingest raw telemetry; map into minimized sanitized features only after licensing and provenance review. |
| UNSW-NB15 | UNSW describes captured network traffic containing normal activity and nine attack types, extracted labelled features, and separate training/test partitions. It says academic/public use is granted but commercial use should be agreed with the authors. [2] | Treat only as an operator-reviewed external-public candidate. Commercial/self-hosted use requires an operator to confirm license suitability before registration. |
| MITRE Caldera | MITRE documents Caldera as an adversary-emulation platform built on ATT&CK, suitable for controlled simulation exercises. [3] | Use only in a controlled lab proof gate. Store derived, sanitized, labelled observations—not operations, payloads, credentials, or command data. |

## Non-negotiable intake controls

External corpus registration is not automation. Before data may be registered, an authorized operator must record its source identity and SHA-256 fingerprint, review applicable licensing, attest that raw telemetry is excluded, and approve the sanitized use. The current implementation permits the controlled PhantomNet BAS fixture corpus for evaluation and calibration work; it does not claim that this corpus represents real-world detection efficacy.

## References

[1]: https://www.unb.ca/cic/datasets/ids-2018.html "CSE-CIC-IDS2018 on AWS — Canadian Institute for Cybersecurity"
[2]: https://research.unsw.edu.au/projects/unsw-nb15-dataset "The UNSW-NB15 Dataset — UNSW"
[3]: https://caldera.readthedocs.io/ "MITRE Caldera Documentation"
