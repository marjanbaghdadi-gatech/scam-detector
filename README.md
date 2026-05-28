# 🛡️ Fraud Awareness Assistant

**An AI-powered tool that helps older adults identify suspicious messages and potential scams.**

Developed by the [Center for Advanced Communications Policy (CACP)](https://cacp.gatech.edu) at **Georgia Institute of Technology** as part of ongoing research on AI, accessibility, and fraud awareness.

---

## 🔗 Live Tool

👉 **[https://marjanbaghdadi-gatech.github.io/scam-detector](https://marjanbaghdadi-gatech.github.io/scam-detector)**

---

## 📋 Overview

The Fraud Awareness Assistant allows users to paste a suspicious text message or upload a screenshot. The tool analyzes the content using a multi-stage AI pipeline and returns a plain-language risk assessment — including what warning signs were detected and what the user should do next.

The tool is specifically designed for **adults aged 60 and older**, with large fonts, plain language, and an accessible layout optimized for both desktop and mobile screens.

### Key Features

- **Text & image input** — paste a message or upload a screenshot
- **Multi-stage parallel analysis** — rules engine, behavioral AI, phone reputation, and domain age detection all run simultaneously
- **Plain-language results** — written at a 6th grade reading level, calm and non-alarming tone
- **Risk level labels** — results shown as Harmless / Likely Harmless / Unclear / Risky / High Risk (no abstract scores shown to users)
- **Tailored next steps** — guidance specific to the detected scam type
- **Domain age detection** — flags newly registered domains used in smishing campaigns
- **Privacy first** — no messages or images are stored or shared
- **Fully responsive** — works on phone, tablet, and desktop

---

## 🔬 Research Context

This tool is part of a research project investigating how AI-powered fraud detection tools can be made accessible and effective for older adults — a demographic disproportionately targeted by financial scams. The project examines:

- Human-AI interaction in fraud detection contexts
- Accessibility of AI tools for aging populations
- The role of plain-language AI explanations in building user trust and awareness

**If you are a researcher or study participant, please complete our feedback survey after using the tool:**

👉 **[Take the Feedback Survey](https://gatech.co1.qualtrics.com/jfe/form/SV_1YRlFkYcZXiWoS2)**

---

## ⚙️ How It Works

The tool sends submitted content to a backend n8n automation pipeline. All detection layers fan out in parallel after the short-circuit check passes, then merge into a single LLM classifier before final scoring.

```
Input (text or image)
    │
    ▼
Entry & Input Handling
    Webhook → Image check → Text extraction → JSON normalization
    │
    ▼
Layer 0 — Pre-Redaction Signals
    URL lookalike detection · Suspicious TLD flagging · Brand impersonation
    Copy-paste link trick · Platform warning capture
    │
    ▼
Short-Circuit Check
    Fast exit for benign messages (< 6 words, no suspicious keywords) → score 5
    │
    ├──────────────────────┬──────────────────────┬────────────────────────┐
    ▼                      ▼                      ▼                        ▼
Layer 1                Layer 2               Layer 3                  Layer 3b
Rules Engine          Behavioral AI         Phone Reputation          Domain Age
15 signal categories  GPT-4.1 narrative     SkipCalls API             WhoisXML API
+ combo bonuses       + tactics analysis    community reports         registration date
    │                      │                      │                        │
    └──────────────────────┴──────────────────────┴────────────────────────┘
                                    │
                                    ▼
                           Signal Merge
                           Collect All Inputs (waits for all branches)
                           Merge All Signals (unified payload)
                                    │
                                    ▼
                           LLM Classifier
                           GPT-4.1 · 13 scam types · red flags · explanation
                                    │
                                    ▼
                           Score Fusion
                           Deterministic JS · floors · boosts · domain age adjustments
                                    │
                                    ▼
                           Structured JSON response
```

### Backend Stack

| Component | Technology |
|---|---|
| Automation pipeline | [n8n](https://n8n.io) |
| LLM (classification + behavioral analysis) | GPT-4.1 |
| Phone reputation lookup | [SkipCalls API](https://skipcalls.com) |
| Domain age lookup | [WhoisXML API](https://whoisxmlapi.com) |
| Hosting | n8n Cloud |

### Detection Layers

**Layer 0 — Pre-Redaction Signals**
Runs before sanitization to preserve URL forensics. Detects lookalike domains (e.g. `usps.com-bcamkozq.vip`), 20+ suspicious TLDs (`.vip`, `.xyz`, `.top`, `.click`), brand names hidden in subdomains, and copy-paste link tricks. Pre-redaction risk is capped at 60 to prevent false positives.

**Layer 1 — Rules Engine**
Deterministic pattern matching across 15 signal categories: urgency language, payment requests, gift card demands, government impersonation, brand impersonation, lottery/prize claims, romance/isolation language, crypto pressure, tech support warnings, and fake billing. Dangerous combinations trigger combo bonuses.

**Layer 2 — Behavioral AI**
GPT-4.1 classifies 8 narrative patterns (grandparent scam, overseas emergency, romance money request, authority pressure, etc.) and scores 8 psychological manipulation tactics (urgency, fear, authority exploitation, isolation, flattery, and others) independently of keywords.

**Layer 3 — Phone Reputation**
Extracts phone numbers and queries SkipCalls. Confirmed scam numbers (+40 to final score); high-risk numbers (+25). Bypassed with zero score when no phone numbers are present.

**Layer 3b — Domain Age Detection**
Queries WhoisXML API for domain registration date when URLs are present. Bypassed entirely when no URLs are present, adding zero latency to phone-only messages.

| Signal | Age Range | Score Added |
|---|---|---|
| Brand new domain | 0–7 days | +40 |
| Very new domain | 8–30 days | +30 |
| New domain | 31–90 days | +15 |
| Established domain | 90+ days | 0 |
| No URLs | — | 0 (bypass) |

### Risk Level Reference

| Score | Label | Meaning |
|---|---|---|
| 0–15 | Harmless | No meaningful scam indicators |
| 16–29 | Likely Harmless | Minor signals, low concern |
| 30–59 | Unclear | Some suspicious elements — verify before acting |
| 60–74 | Risky | Clear scam pattern — do not click links |
| 75–100 | High Risk | Strong indicators of a known scam type |

> **Note:** Numeric scores are used internally for decision-making only. The tool displays only the plain-language risk level label to users.

---

## 🗂️ Repository Structure

```
scam-detector/
├── index.html                          # Main tool page
├── styles.css                          # Global styles
├── script.js                           # Tool logic, API calls, result rendering
├── pages/
│   └── page.css                        # Shared stylesheet for feed pages
├── latest-scam-trends/
│   ├── latest-trends.html              # Latest scam trends page
│   └── data/
│       └── scams.json                  # Scam feed data (auto-updated weekly by n8n)
├── fraud-victim-stories/
│   ├── victim-stories.html             # Victim stories page
│   └── data/
│       └── stories.json                # Victim stories data (auto-updated by n8n)
├── scam_tester.py                      # Automated test runner (33 test cases)
└── README.md                           # This file
```

### Backend Data URLs (GitHub Contents API)

| File | GitHub Contents API URL |
|---|---|
| Scam feed | `https://api.github.com/repos/marjanbaghdadi-gatech/scam-detector/contents/latest-scam-trends/data/scams.json` |
| Victim stories | `https://api.github.com/repos/marjanbaghdadi-gatech/scam-detector/contents/fraud-victim-stories/data/stories.json` |

---

## 🚀 Running Locally

This is a static front-end — no build step required.

```bash
git clone https://github.com/marjanbaghdadi-gatech/scam-detector
cd scam-detector
```

Then open `index.html` in your browser. The tool connects to a hosted n8n backend at runtime — no local backend setup is needed.

> **Note:** The backend webhook URL is hardcoded in `script.js`. The backend is hosted on n8n Cloud and is not included in this repository.

### Running Tests

```bash
# Run all 33 test cases
python scam_tester.py

# Run by tag (e.g. domain age detection only)
python scam_tester.py --tag domain_age
```

---

## 🔒 Privacy

- No user messages, images, or personal data are stored on any server
- All content submitted to the tool is processed in real time and immediately discarded
- No account or login is required
- No cookies or tracking are used

---

## 📬 Contact

**Marjan Baghdadi**
Center for Advanced Communications Policy
Georgia Institute of Technology
📧 [marjan.baghdadi@gatech.edu](mailto:marjan.baghdadi@gatech.edu)

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

## ⚠️ Disclaimer

This tool is intended for **educational and research purposes only**. It is not a substitute for professional legal or financial advice. Results are probabilistic and may not be accurate in all cases. When in doubt, verify through official sources.
