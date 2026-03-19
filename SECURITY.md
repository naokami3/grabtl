# Security Policy

## Reporting a Vulnerability

**Please do NOT open public GitHub issues for security vulnerabilities.**

Use [GitHub Private Vulnerability Reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability):

1. Go to the **Security** tab of this repository
2. Click **Report a vulnerability**
3. Provide a detailed description of the issue

### Response Timeline
- **Acknowledgment:** Within 48 hours
- **Assessment:** Within 72 hours
- **Critical fix:** Target 7 days from report
- **Non-critical fix:** Target next scheduled release

### Scope

**In scope:**
- API key leakage or unintended exposure
- Unintended network communication (data sent to non-declared endpoints)
- Vulnerabilities in our code that could be exploited by malicious input
- Authentication or authorization bypasses

**Out of scope:**
- Vulnerabilities in Ollama, Windows OCR, or third-party translation APIs
- Issues requiring physical access to an unlocked machine
- Issues requiring prior compromise of the user's Windows account (this is an accepted limitation of DPAPI — see [docs/security-design.md](docs/security-design.md))
- Social engineering attacks

## Security Design

For details on our security architecture, API key storage, and known limitations, see [docs/security-design.md](docs/security-design.md).

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | ✅ |
| Previous minor | ✅ (critical fixes only) |
| Older | ❌ |
