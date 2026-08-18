# World Intel MCP Assessment Notes

Source reviewed: https://github.com/marc-shade/world-intel-mcp (reviewed 2026-08-18).

The repository presents a Python MCP server run in stdio mode with the `world-intel-mcp` command. It exposes approximately 120 tools spanning real-time global intelligence domains including markets, SEC filings, conflict, military activity, cyber, climate, news, geofences, daily digests, strategic posture, and cited situation briefs.

The server fetches source data through an HTTPX-based fetcher and describes source-level retries, rate limiting, caching/stale fallback, and circuit breakers. It supports optional API keys for several sources such as ACLED, NASA FIRMS, EIA, Cloudflare, FRED, and OpenSky; public/free sources can operate without those credentials.

PhantomNet integration should be read-only and advisory. The integration must not provide World Intel outputs directly to enforcement actions. Intelligence-derived events should remain untrusted until correlation and policy review occur, with provenance/citations preserved, source failures tolerated, and no external secrets committed to the PhantomNet repository.

Potential integration patterns:

1. A custom MCP connector enables agents to query World Intel tools directly for enrichment and analyst briefs.
2. A PhantomNet service adapter calls a selected, allowlisted subset of World Intel intelligence tools and records cited outputs as enrichment only.

A connector requires an explicit user-approved configuration change. The public repository documentation must be used to verify exact package installation and MCP transport details before creating a connector draft.

## README-confirmed configuration

The raw README confirms that the server is installed from source using `pip install -e .` and started with the `world-intel-mcp` stdio command. Its documented client configuration is a simple stdio MCP server with `command: world-intel-mcp` and no required core credentials.

The following credentials are optional and should remain outside the PhantomNet repository: `ACLED_ACCESS_TOKEN`, `NASA_FIRMS_API_KEY`, `EIA_API_KEY`, `CLOUDFLARE_API_TOKEN`, `FRED_API_KEY`, `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET`, `OLLAMA_API_URL`, `OLLAMA_MODEL`, and `WORLD_INTEL_LOG_LEVEL`.

This makes a no-secret, read-only local stdio connector technically viable for basic public-source enrichment. A user-approved connector configuration is still required before activating it for agent use.

## Source and connector compatibility findings

A read-only clone was inspected at commit `9254192d83f88bd7e5312b074c11f09398b84ca9` (2026-08-16). The project is MIT licensed, supports Python 3.11+, and declares the `mcp>=1.8.0,<2.0.0` SDK. Its `world-intel-mcp` CLI command maps to `world_intel_mcp.server:run`, which uses stdio transport.

The current task connector configuration could not be inspected because the connector configuration service returned `403 Forbidden`. No connector was created, enabled, modified, or invoked. A user-approved MCP connector would need access to the connector configuration service; alternatively, a constrained project-side stdio client can be added as an optional dependency.
