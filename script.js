const WEBHOOK_URL = "https://mbaghdadi6g.app.n8n.cloud/webhook/fraud-check";
const ACCURACY_WEBHOOK_URL = "https://mbaghdadi6g.app.n8n.cloud/webhook/accuracy-feedback";
 
const textInput       = document.getElementById("textInput");
const charCount       = document.getElementById("charCount");
const imageInput      = document.getElementById("imageInput");
const dropZone        = document.getElementById("dropZone");
const fileName        = document.getElementById("fileName");
const imagePreviewWrap = document.getElementById("imagePreviewWrap");
const imagePreview     = document.getElementById("imagePreview");
const clearImageBtn    = document.getElementById("clearImageBtn");
const analyzeTextBtn  = document.getElementById("analyzeTextBtn");
const analyzeImageBtn = document.getElementById("analyzeImageBtn");
 
const loadingPanel    = document.getElementById("loadingPanel");
const loadingHeadline = document.getElementById("loadingHeadline");
const lstep1          = document.getElementById("lstep1");
const lstep2          = document.getElementById("lstep2");
const lstep3          = document.getElementById("lstep3");
 
const accuracyCard        = document.getElementById("accuracyCard");
const accuracyThanks      = document.getElementById("accuracyThanks");

const resultsPanel        = document.getElementById("resultsPanel");
const riskLabel           = document.getElementById("riskLabel");
const riskBadge = document.getElementById("riskBadge");
const gaugeNeedle         = document.getElementById("gaugeNeedle");
const redFlagsList        = document.getElementById("redFlagsList");
const nextStepsList       = document.getElementById("nextStepsList");
const flagCount = document.getElementById("flagCount");
const viewFullBtn         = document.getElementById("viewFullBtn");
const fullAnalysis        = document.getElementById("fullAnalysis");
const explanationText     = document.getElementById("explanationText");
const plainExplanationText = document.getElementById("plainExplanationText");
const disclaimerText      = document.getElementById("disclaimerText");
 
 
let selectedImageFile = null;
let stepTimer = null;
let lastInputType = "text";
let lastResultContext = null;

// ── Theme toggle ──────────────────────────────────────
const themeBtn = document.querySelector(".theme-btn");
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
  themeBtn.textContent = "☀";
}
themeBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  const isDark = document.body.classList.contains("dark");
  themeBtn.textContent = isDark ? "☀" : "☾";
  localStorage.setItem("theme", isDark ? "dark" : "light");
});


// ── Char counter ─────────────────────────────────────
textInput.addEventListener("input", () => {
  charCount.textContent = `${textInput.value.length} / 3000`;
});
 
// ── Pre-fill from URL parameter (from scams page "Test this scam" button) ──
window.addEventListener("load", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const prefilledMessage = urlParams.get("message");
  if (prefilledMessage && textInput) {
    textInput.value = prefilledMessage;
    if (charCount) charCount.textContent = prefilledMessage.length + " / 3000";
    setTimeout(() => textInput.scrollIntoView({ behavior: "smooth", block: "center" }), 300);
  }
});

// ── Image selection ──────────────────────────────────
imageInput.addEventListener("change", () => {
  selectedImageFile = imageInput.files[0] || null;
  showImagePreview(selectedImageFile);
});
 
dropZone.addEventListener("click", () => {
  if (!selectedImageFile) imageInput.click();
});
 
dropZone.addEventListener("keydown", e => {
  if ((e.key === "Enter" || e.key === " ") && !selectedImageFile) imageInput.click();
});
 
["dragenter", "dragover"].forEach(e => {
  dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add("drag-over"); });
});
["dragleave", "drop"].forEach(e => {
  dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove("drag-over"); });
});
 
dropZone.addEventListener("drop", event => {
  selectedImageFile = event.dataTransfer.files[0];
  if (!selectedImageFile) return;
  if (!selectedImageFile.type.startsWith("image/")) {
    alert("Please upload an image file.");
    selectedImageFile = null;
    return;
  }
  showImagePreview(selectedImageFile);
});
 
window.addEventListener("paste", event => {
  for (const item of event.clipboardData?.items || []) {
    if (item.type.startsWith("image/")) {
      selectedImageFile = item.getAsFile();
      showImagePreview(selectedImageFile);
      break;
    }
  }
});
 
// ── Image preview ─────────────────────────────────────
function showImagePreview(file) {
  if (!file) return;
  const url = URL.createObjectURL(file);
  imagePreview.src = url;
  imagePreview.onload = () => URL.revokeObjectURL(url);
  fileName.textContent = file.name || "Pasted image";
  imagePreviewWrap.classList.remove("hidden");
  dropZone.style.display = "none";
}
 
function clearImage() {
  selectedImageFile = null;
  imagePreview.src = "";
  fileName.textContent = "";
  imagePreviewWrap.classList.add("hidden");
  dropZone.style.display = "";
  imageInput.value = "";
}
 
// ── Clear image ───────────────────────────────────────
clearImageBtn.addEventListener("click", clearImage);
 
// ── Analyze text ──────────────────────────────────────
analyzeTextBtn.addEventListener("click", async () => {
  const rawText = textInput.value.trim();
  if (!rawText) { alert("Please paste a suspicious message first."); return; }

  lastInputType = "text";
  showLoading("Analyzing your message…");
  setLoading(analyzeTextBtn, true);
 
  try {
    const response = await fetch(WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: rawText })
    });
    if (!response.ok) throw new Error("The workflow did not return a successful response.");
    renderResults(await response.json());
  } catch (error) {
    showError(error);
  } finally {
    hideLoading();
    setLoading(analyzeTextBtn, false, "Check this message");
  }
});
 
// ── Analyze image ─────────────────────────────────────
analyzeImageBtn.addEventListener("click", async () => {
  if (!selectedImageFile) { alert("Please upload or paste a screenshot first."); return; }
  if (selectedImageFile.size > 10 * 1024 * 1024) { alert("Please upload an image smaller than 10 MB."); return; }

  lastInputType = "image";
  showLoading("Reading your screenshot…");
  setLoading(analyzeImageBtn, true);
 
  const formData = new FormData();
  formData.append("image", selectedImageFile);
 
  try {
    const response = await fetch(WEBHOOK_URL, { method: "POST", body: formData });
    if (!response.ok) throw new Error("The workflow did not return a successful response.");
    renderResults(await response.json());
  } catch (error) {
    showError(error);
  } finally {
    hideLoading();
    setLoading(analyzeImageBtn, false, "Check this image");
  }
});
 
// ── Toggle full analysis ──────────────────────────────
viewFullBtn.addEventListener("click", () => {
  const isHidden = fullAnalysis.classList.toggle("hidden");
  viewFullBtn.setAttribute("aria-expanded", String(!isHidden));
  viewFullBtn.textContent = isHidden ? "Full explanation ↓" : "Hide explanation ↑";
});
 
// ── Loading panel ─────────────────────────────────────
function showLoading(headline) {
  loadingHeadline.textContent = headline;
  accuracyCard.classList.add("hidden");
  resultsPanel.classList.add("hidden");
  loadingPanel.classList.remove("hidden");
  loadingPanel.scrollIntoView({ behavior: "smooth", block: "start" });
 
  // Reset steps
  [lstep1, lstep2, lstep3].forEach(s => s.classList.remove("active", "done"));
 
  // Sequence: step 1 active immediately, step 2 after ~4s, step 3 after ~9s
  lstep1.classList.add("active");
  stepTimer = setTimeout(() => {
    lstep1.classList.replace("active", "done");
    lstep2.classList.add("active");
  }, 4000);
  stepTimer = setTimeout(() => {
    lstep2.classList.replace("active", "done");
    lstep3.classList.add("active");
  }, 9000);
}
 
function hideLoading() {
  clearTimeout(stepTimer);
  [lstep1, lstep2, lstep3].forEach(s => s.classList.remove("active"));
  loadingPanel.classList.add("hidden");
}
 
// ── Render results ────────────────────────────────────
function renderResults(raw) {
  // n8n returns an array — unwrap it
  const data = Array.isArray(raw) ? raw[0] : raw;
  const score     = Math.max(0, Math.min(Number(data.risk_score ?? 0), 100));
  const level     = normalizeRiskLevel(data.risk_level, score);
  const cls       = riskClass(level);
 
  // Score used silently for gauge needle only — not shown to user
  gaugeNeedle.style.transform = `rotate(${-180 + score * 1.8}deg)`;
 
  // Human-readable label
  const labelText = level === "likely risky"    ? "High Risk"
                  : level === "unclear"          ? "Unclear"
                  : "Likely Harmless";
  riskLabel.textContent = labelText;
  riskLabel.className   = `risk-label ${cls}`;
 
  if(riskBadge) riskBadge.textContent = level === "likely risky" ? "⚠ High Risk" : titleCase(level);
  if(riskBadge) riskBadge.className   = `risk-badge ${cls}`;
 
 
  // Combine red flags with behavioral tactics for richer warning signs
  const redFlags = Array.isArray(data.red_flags) ? data.red_flags : [];
  const activeTactics = Array.isArray(data.active_tactics) ? data.active_tactics : [];
 
  // Convert behavioral tactic keys to plain readable labels
  const tacticLabels = {
    urgency_creation:        "Creates artificial urgency or time pressure",
    fear_induction:          "Uses threats or fear to pressure you",
    authority_exploitation:  "Impersonates a trusted authority figure",
    isolation_tactic:        "Asks you to keep this secret from others",
    trust_building:          "Uses excessive warmth or flattery before a request",
    too_good_to_be_true:     "Makes an offer that seems unrealistically good",
    reciprocity_manipulation:"Creates a sense of obligation or debt",
    scarcity_pressure:       "Claims this is a limited or exclusive opportunity",
    emotional_exploitation:  "Plays on your emotions — love, fear, guilt, or sympathy",
    action_bypass:           "Pressures you to act before you can think or verify",
  };
 
  // Only show behavioral tactics not already covered by red flags
  const behavioralWarnings = activeTactics
    .filter(t => tacticLabels[t])
    .map(t => tacticLabels[t])
    .filter(label => !redFlags.some(f => f.toLowerCase().includes(label.toLowerCase().slice(0, 20))));
 
  // Phone reputation warnings
  const phoneWarnings = [];
  if (data.phone_risk_signal === "confirmed_scam_number") {
    phoneWarnings.push("This phone number has been reported as a scam number by many people");
  } else if (data.phone_risk_signal === "high_risk_number") {
    phoneWarnings.push("This phone number has been flagged as suspicious or spam");
  } else if (data.phone_risk_signal === "reported_spam_number") {
    phoneWarnings.push("This phone number has been reported as spam");
  }

  const allWarnings = [...redFlags, ...behavioralWarnings, ...phoneWarnings];
 
  // Show behavioral summary as an extra warning if novel scam detected and no other warnings
  if (allWarnings.length === 0 && data.behavioral_summary && data.behavioral_risk_score > 40) {
    allWarnings.push(data.behavioral_summary);
  }
 
  renderList(redFlagsList, allWarnings, "No major red flags detected.");
  renderList(nextStepsList, data.recommended_next_steps, "Verify through an official source.");
 
  // Flag count includes both keyword and behavioral warnings
  if(flagCount) flagCount.textContent = allWarnings.length;
 
  explanationText.textContent =
    data.plain_language_explanation || "The tool checked this message for common scam patterns and warning signs.";
 
  const scamType = data.scam_type && data.scam_type !== "none_detected"
    ? "Detected pattern: " + data.scam_type.replace(/_/g, " ") + ". "
    : "";
 
  // Add behavioral summary if present and novel scam detected
  const behavioralNote = data.behavioral_summary && data.behavioral_risk_score > 40
    ? " Behavioral analysis: " + data.behavioral_summary
    : "";
 
  plainExplanationText.textContent =
    scamType + (data.summary || "Use this result to help decide what to do next.") + behavioralNote;
 
  disclaimerText.textContent =
    data.disclaimer || "This is an educational assessment. When in doubt, verify through an official source.";
 
  // Store context for accuracy vote
  lastResultContext = {
    risk_level: level,
    risk_score: score,
    input_type: lastInputType,
  };

  // Reset and show accuracy card
  accuracyThanks.classList.add("hidden");
  document.querySelectorAll(".accuracy-btn").forEach(b => {
    b.disabled = false;
    b.classList.remove("selected");
  });
  accuracyCard.classList.remove("hidden");

  resultsPanel.classList.remove("hidden");
  resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderList(container, items, fallback) {
  container.innerHTML = "";
  (Array.isArray(items) && items.length ? items : [fallback]).forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  });
}
 
// ── Accuracy feedback ─────────────────────────────────
document.querySelectorAll(".accuracy-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    const vote = btn.dataset.vote;
    document.querySelectorAll(".accuracy-btn").forEach(b => {
      b.disabled = true;
      b.classList.remove("selected");
    });
    btn.classList.add("selected");
    accuracyThanks.classList.remove("hidden");

    if (!lastResultContext) return;
    try {
      await fetch(ACCURACY_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          timestamp: new Date().toISOString(),
          vote,
        }),
      });
    } catch (_) {
      // best-effort — don't surface network errors to the user
    }
  });
});

// ── Error state ───────────────────────────────────────
function showError(error) {
  riskLabel.textContent    = "—";
  riskLabel.className     = "risk-label";
  if(riskBadge) riskBadge.textContent    = "Error";
  if(riskBadge) riskBadge.className      = "risk-badge medium";
  redFlagsList.innerHTML   = "";
  nextStepsList.innerHTML  = "";
  if(flagCount) flagCount.textContent    = "0";
  explanationText.textContent     = error.message;
  plainExplanationText.textContent = "";
  disclaimerText.textContent       = "";
  accuracyCard.classList.add("hidden");
  resultsPanel.classList.remove("hidden");
  resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Helpers ───────────────────────────────────────────
function setLoading(button, isLoading, label) {
  button.disabled = isLoading;
  if (isLoading) {
    button.classList.add("loading");
  } else {
    button.classList.remove("loading");
    button.textContent = label;
  }
}
 
function normalizeRiskLevel(level, score) {
  const c = String(level || "").toLowerCase();
  if (c.includes("harmless"))               return "likely harmless";
  if (c.includes("risky") || c.includes("high")) return "likely risky";
  if (c.includes("unclear") || c.includes("medium")) return "unclear";
  if (score >= 60) return "likely risky";
  if (score >= 30) return "unclear";
  return "likely harmless";
}
 
function riskClass(level) {
  if (level === "likely harmless") return "low";
  if (level === "unclear")         return "medium";
  return "high";
}
 
function titleCase(text) {
  return String(text).split(" ")
    .map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}
 
function escapeHTML(value) {
  return String(value)
    .replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}
 
