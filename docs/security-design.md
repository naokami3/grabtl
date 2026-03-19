# Security Design — grabtl

## Overview

This document describes the security architecture of grabtl.
We follow the principle of **transparent security** — openly documenting both our protections and their known limitations.

## Threat Model

**What we protect:** Third-party API keys (DeepL, Claude, GPT, Gemini) stored on the user's machine.

**Threat level:** Low-to-moderate. API keys for translation services carry limited financial risk (typically free tier or usage-capped). This is not banking software.

**What we do NOT protect against:**
- A compromised Windows user account (if malware runs as your user, it can read anything you can)
- Physical access to an unlocked machine
- Vulnerabilities in the OS itself or in Ollama

## Three-Tier Architecture

| Tier | Mode | API Key | Network | Risk |
|------|------|---------|---------|------|
| 0 | Local (argostranslate + Windows OCR) | Not required | None | Minimal |
| 1 | Local LLM (Ollama) | Not required | localhost only | Minimal |
| 2 | Cloud API (DeepL, Claude, etc.) | Required (BYOK) | HTTPS to API provider | Low |

**Recommendation:** Start with Tier 0. No configuration, no API keys, no network traffic.

## API Key Storage

### Method
We use Python's `keyring` library, which on Windows delegates to **Windows Credential Manager** backed by **DPAPI** (Data Protection API).

This is the same approach used by:
- **VS Code** — SecretStorage API (Electron safeStorage → Chromium OSCrypt → DPAPI)
- **Chrome** — saved passwords (OSCrypt → DPAPI)
- **Git Credential Manager** — stored tokens

### What DPAPI provides
- API keys are encrypted at rest using a key derived from your Windows login credentials
- Keys are tied to your specific Windows user account and machine
- Keys are NOT stored in plaintext in any configuration file

### Known Limitations (we are transparent about these)
- **No per-application isolation:** Any process running as the same Windows user can theoretically call DPAPI to decrypt stored credentials. This is a Windows design decision, not a bug (see [MITRE ATT&CK T1555.004](https://attack.mitre.org/techniques/T1555/004/), [Raymond Chen's explanation](https://devblogs.microsoft.com/oldnewthing/20230206-00/?p=107797)).
- **Python memory constraints:** Python strings are immutable; we cannot guarantee secure memory zeroing after use (no equivalent of C's `SecureZeroMemory`).
- **Open source:** Since the code is public, any additional encryption entropy would be visible in the source, providing no real security benefit ("security through obscurity" is not security).

### Risk Mitigation
Rather than pursuing technically impossible "perfect" key protection, we minimize the impact of potential key exposure:

1. **Use free-tier API keys:** DeepL API Free provides 500,000 characters/month at no cost. If leaked, financial impact is zero.
2. **Set usage limits:** For paid APIs (Claude, GPT), we guide users to create keys with spending caps.
3. **Provide rotation guides:** Settings UI includes direct links to each provider's key regeneration page.
4. **Communication logging:** Users can inspect exactly what data is sent to API providers via the built-in communication log.

## Network Communication

### Allowed Endpoints
Each Translator implementation declares its `allowed_endpoints` property. The application only communicates with these domains:

| Engine | Endpoints | Protocol |
|--------|-----------|----------|
| argostranslate | None (local) | — |
| Ollama | `127.0.0.1:11434` | HTTP (localhost) |
| DeepL | `api-free.deepl.com`, `api.deepl.com` | HTTPS |
| Claude | `api.anthropic.com` | HTTPS |
| Gemini | `generativelanguage.googleapis.com` | HTTPS |

### Enforcement
- HTTPS certificate verification is NEVER disabled (`verify=False` is prohibited by lint rules)
- CI tests detect outbound connections to non-allowlisted domains
- Communication log UI shows all API requests in real-time (API keys are masked)

### Ollama Security Note
Ollama may bind to `0.0.0.0:11434` by default, making it accessible from the local network. We recommend:
```
OLLAMA_HOST=127.0.0.1:11434
```
Our application hardcodes the connection target to `127.0.0.1`.

## Screen Capture Privacy

- Captured images are processed in memory only; never written to disk
- When using cloud APIs (Tier 2), OCR text extracted from screenshots is sent to the translation provider
- Users are informed at first use of Tier 2: "The text in your selected area will be sent to [provider name]"
- Optional: Preview OCR text before sending

## Supply Chain Security

- All dependencies are pinned with hashes in `requirements-lock.txt`
- Weekly `pip-audit` scans for known vulnerabilities
- `pip-licenses` checks ensure all dependencies remain MIT-compatible
- Release binaries include SHA256 hashes in release notes
- GitHub Actions CI/CD builds are public and reproducible

## Vulnerability Reporting

See [SECURITY.md](../SECURITY.md) for reporting procedures.

- **Report via:** GitHub Private Vulnerability Reporting (Security → Report a vulnerability)
- **Do NOT** open public issues for security vulnerabilities
- **Response target:** Acknowledgment within 48 hours, patch within 7 days for critical issues
- **Scope:** This application only. Vulnerabilities in Ollama, Windows OCR, or translation API providers are out of scope.
