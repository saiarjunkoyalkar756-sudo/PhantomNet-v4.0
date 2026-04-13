# Frontend UI Blueprints for Autonomous Vulnerability Management

This document outlines conceptual new UI pages and components to be developed within the `dashboard_frontend/` to support the Autonomous Vulnerability Management capabilities.

---

## 1. Vulnerability Dashboard (`/vulnerabilities`)

**Objective:** Provide a high-level overview of the organization's vulnerability posture, key metrics, and trending issues.

**Key Components & Features:**

*   **Overview Widgets:**
    *   Total Vulnerabilities (Open, Triaged, Resolved, Critical, High, Medium, Low).
    *   Vulnerabilities by Asset Criticality.
    *   Vulnerabilities by CVE Severity (CVSS score distribution).
    *   Top 10 Most Vulnerable Assets.
    *   Top 10 Most Prevalent CVEs.
    *   Trends: New vulnerabilities over time, resolution rate.
*   **Vulnerability List:**
    *   Table view of all detected vulnerabilities (`GET /vulnerability-management/vulnerabilities`).
    *   Columns: Vulnerability ID, Asset ID, CVE ID, Status, Priority (AI-generated), Detected At, Patch Available.
    *   Search, filter, and sort capabilities (by asset, CVE, status, priority, etc.).
    *   Actions: View Details, Generate Patch Recommendation, Change Status.
*   **Filters:** Global filters for criticality, status, asset type, OS, etc.

---

## 2. Asset View with Associated Vulnerabilities (`/assets/{asset_id}`)

**Objective:** Display detailed information about a specific asset, including its identified vulnerabilities and patch recommendations. This would be an enhancement to an existing Asset Inventory UI or a new dedicated page.

**Key Components & Features:**

*   **Asset Details Card:**
    *   Basic info: Asset Name, Type, IP Addresses, Hostnames, OS, Criticality.
    *   Last Seen, last scanned, agent status.
*   **Installed Software List:** List of detected software and versions.
*   **Associated Vulnerabilities Table:**
    *   Table view of vulnerabilities specific to this asset (`GET /vulnerability-management/vulnerabilities?asset_id={asset_id}`).
    *   Columns: CVE ID, Description, Severity, Priority, Status, Remediation.
    *   Actions: View CVE Details, Get Patch Recommendation.
*   **Patch Recommendations List:**
    *   List of `PatchRecommendation` objects relevant to this asset's vulnerabilities.
    *   Each recommendation shows: Patch Name, Recommended Action, Reasoning, Priority Score, Generated At.
    *   Actions: Initiate Patch Deployment (conceptual, integrates with SOAR/CMDB), Mark as Applied, Dismiss.

---

## 3. Patch Management/Recommendation UI (`/patch-management`)

**Objective:** Centralized view for managing and acting upon AI-generated patch recommendations.

**Key Components & Features:**

*   **Recommendation List:**
    *   Table view of all pending `PatchRecommendation` objects (`GET /vulnerability-management/patch_recommendations`).
    *   Columns: Recommendation ID, Vulnerability ID, Asset ID, Patch Name, Action, Priority, Generated At.
    *   Filters: By asset, vulnerability, recommended action, priority.
    *   Actions: View Vulnerability Details, View Asset Details, Approve & Deploy (integrates with SOAR), Dismiss.
*   **AI Prioritization Insights:**
    *   Explanation of why a patch was prioritized (e.g., "High CVSS score, critical asset, known exploit").
*   **Deployment Status (Conceptual):** Integration with SOAR or change management systems to track patch deployment status.

---

## Technical Considerations for Frontend Developers:

*   **API Endpoints:** Frontend will interact with `/vulnerability-management/assets`, `/vulnerability-management/scan/assets`, `/vulnerability-management/vulnerabilities`, `/vulnerability-management/cve`, `/vulnerability-management/patch_recommendations`.
*   **Data Visualization:** Use charting libraries (e.g., Chart.js, Recharts) for dashboard widgets.
*   **Contextual Linking:** Ensure easy navigation between assets, vulnerabilities, CVE details, and patch recommendations.
*   **Security:** Implement RBAC for who can view, trigger scans, and approve/deploy patches.
