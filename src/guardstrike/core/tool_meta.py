"""Curated, display-only metadata for the built-in security tools.

Tool classes carry no description/category, so this map powers `tools list`
and `tools info`. Tools without an entry fall back to a graceful default —
the map need not cover every registered tool.
"""

from __future__ import annotations

TOOL_META: dict[str, dict[str, str]] = {
    # recon
    "subfinder": {"description": "Passive subdomain enumeration", "category": "recon"},
    "amass": {"description": "In-depth subdomain/asset discovery", "category": "recon"},
    "dnsrecon": {"description": "DNS enumeration and record discovery", "category": "recon"},
    "theharvester": {"description": "OSINT emails/hosts/subdomains gathering", "category": "recon"},
    "shodan": {"description": "Internet-exposed host intelligence lookup", "category": "recon"},
    "httpx": {"description": "Fast HTTP prober and tech fingerprint", "category": "recon"},
    "whatweb": {"description": "Web technology fingerprinting", "category": "recon"},
    "cariddi": {"description": "Crawl endpoints/secrets from URLs", "category": "recon"},
    # network
    "nmap": {"description": "Network port and service scanner", "category": "network"},
    "masscan": {"description": "High-speed mass port scanner", "category": "network"},
    # tls
    "testssl": {"description": "TLS/SSL configuration scanner", "category": "tls"},
    "sslyze": {"description": "Fast TLS configuration analyzer", "category": "tls"},
    "wafw00f": {"description": "Web application firewall detection", "category": "web"},
    # web / vuln
    "nuclei": {"description": "Template-based vulnerability scanner", "category": "web"},
    "nikto": {"description": "Web server vulnerability scanner", "category": "web"},
    "sqlmap": {"description": "SQL injection detection and exploitation", "category": "web"},
    "wpscan": {"description": "WordPress security scanner", "category": "web"},
    "cmseek": {"description": "CMS detection and enumeration", "category": "web"},
    "xsstrike": {"description": "XSS detection and fuzzing", "category": "web"},
    "gobuster": {"description": "Directory/DNS/vhost brute forcing", "category": "web"},
    "ffuf": {"description": "Fast web fuzzer", "category": "web"},
    "arjun": {"description": "HTTP parameter discovery", "category": "web"},
    "zap": {"description": "OWASP ZAP web app scanner", "category": "web"},
    "burp": {"description": "Burp Suite scan integration", "category": "web"},
    # api
    "schemathesis": {
        "description": "OpenAPI/GraphQL property-based API testing",
        "category": "api",
    },
    "restler": {"description": "Stateful REST API fuzzing", "category": "api"},
    "graphw00f": {"description": "GraphQL engine fingerprinting", "category": "api"},
    "clairvoyance": {"description": "GraphQL schema extraction", "category": "api"},
    "jwt_tool": {"description": "JWT analysis and attacks", "category": "api"},
    # secrets / code
    "gitleaks": {"description": "Secret scanning in git repos", "category": "secrets"},
    "trufflehog": {"description": "Verified secret detection", "category": "secrets"},
    "semgrep": {"description": "Static analysis / SAST", "category": "code"},
    "dependency-check": {"description": "Dependency vulnerability (SCA) scan", "category": "code"},
    "trivy": {"description": "Container/IaC vulnerability scanner", "category": "code"},
    "grype": {"description": "Container image vulnerability scanner", "category": "code"},
    "syft": {"description": "SBOM generation", "category": "code"},
    # cloud / k8s
    "prowler": {"description": "Cloud (AWS/Azure/GCP) security assessment", "category": "cloud"},
    "scoutsuite": {"description": "Multi-cloud security auditing", "category": "cloud"},
    "kube-bench": {"description": "Kubernetes CIS benchmark checks", "category": "cloud"},
    # mobile
    "mobsf": {"description": "Mobile app security framework", "category": "mobile"},
    "apkleaks": {"description": "APK secret/endpoint scanning", "category": "mobile"},
    "objection": {"description": "Runtime mobile exploration (Frida)", "category": "mobile"},
    # ad / network auth
    "bloodhound": {"description": "Active Directory attack-path mapping", "category": "ad"},
    "crackmapexec": {"description": "Network/AD post-exploitation", "category": "ad"},
    "kerbrute": {"description": "Kerberos user/password bruteforce", "category": "ad"},
    "impacket-secretsdump": {"description": "Dump AD/host secrets", "category": "ad"},
    # ai / llm
    "garak": {"description": "LLM vulnerability scanner", "category": "ai"},
    "pyrit": {"description": "LLM risk identification toolkit", "category": "ai"},
    "prompt_fuzz": {"description": "Prompt-injection fuzzing", "category": "ai"},
    # misc
    "playwright_screenshot": {"description": "Headless page screenshotting", "category": "recon"},
}


def tool_summary(name: str) -> dict[str, str]:
    """Description + category for a tool, with a graceful default."""
    meta = TOOL_META.get(name, {})
    return {
        "description": meta.get("description", ""),
        "category": meta.get("category", "other"),
    }
