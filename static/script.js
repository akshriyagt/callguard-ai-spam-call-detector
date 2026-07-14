const SAMPLES = {
  lottery: {
    phone_number: "+919999000011",
    transcript: "Congratulations! You are the lucky winner of our lucky draw cash prize, share your otp to claim",
    calls_per_day: 12,
    avg_call_duration: 20,
    is_international: false,
  },
  otp: {
    phone_number: "+918888000022",
    transcript: "This is your bank calling, your card is blocked, kindly share otp to unblock your debit card now",
    calls_per_day: 6,
    avg_call_duration: 15,
    is_international: false,
  },
  loan: {
    phone_number: "+919876543210",
    transcript: "Sir we are offering instant loan approved with zero interest loan, no documents required",
    calls_per_day: 25,
    avg_call_duration: 18,
    is_international: false,
  },
  ham: {
    phone_number: "+919845098450",
    transcript: "Hi, it's mom, just calling to check how you are doing",
    calls_per_day: 1,
    avg_call_duration: 180,
    is_international: false,
  },
};

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const s = SAMPLES[chip.dataset.sample];
    document.getElementById("phoneNumber").value = s.phone_number;
    document.getElementById("transcript").value = s.transcript;
    document.getElementById("callsPerDay").value = s.calls_per_day;
    document.getElementById("avgDuration").value = s.avg_call_duration;
    document.getElementById("isInternational").checked = s.is_international;
  });
});

const form = document.getElementById("callForm");
const answerBtn = document.getElementById("answerBtn");
const ringVisual = document.getElementById("ringVisual");
const ringLabel = document.getElementById("ringLabel");

const gaugeFill = document.getElementById("gaugeFill");
const gaugeScore = document.getElementById("gaugeScore");
const mlBar = document.getElementById("mlBar");
const ruleBar = document.getElementById("ruleBar");
const mlVal = document.getElementById("mlVal");
const ruleVal = document.getElementById("ruleVal");
const verdictCard = document.getElementById("verdictCard");
const verdictLabel = document.getElementById("verdictLabel");
const verdictReasons = document.getElementById("verdictReasons");
const ivrTranscript = document.getElementById("ivrTranscript");
const callHistory = document.getElementById("callHistory");

const GAUGE_CIRCUMFERENCE = 251.2;

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function setGauge(score, color) {
  const offset = GAUGE_CIRCUMFERENCE - (GAUGE_CIRCUMFERENCE * Math.min(score, 100)) / 100;
  gaugeFill.style.strokeDashoffset = offset;
  gaugeFill.style.stroke = color;
  gaugeScore.textContent = Math.round(score);
}

async function playIvr(lines) {
  ivrTranscript.innerHTML = "";
  for (let i = 0; i < lines.length; i++) {
    const div = document.createElement("div");
    div.className = "ivr-line";
    div.innerHTML = `<span class="ivr-index">AI · step ${i + 1}</span>${lines[i]}`;
    ivrTranscript.appendChild(div);
    await sleep(450);
  }
}

function addHistoryItem(result) {
  const li = document.createElement("li");
  li.className = `history-item ${result.is_spam ? "spam" : "safe"}`;
  li.innerHTML = `
    <span>${result.phone_number}</span>
    <span class="history-badge ${result.is_spam ? "spam" : "safe"}">${result.is_spam ? "Spam" : "Genuine"} · ${result.final_score}</span>
  `;
  callHistory.prepend(li);
}

async function renderResult(result) {
  const spamColor = "#FF5D5D";
  const safeColor = "#3DDC97";
  const color = result.is_spam ? spamColor : safeColor;

  setGauge(result.final_score, color);
  mlBar.style.width = `${result.ml_score}%`;
  ruleBar.style.width = `${result.rule_score}%`;
  mlVal.textContent = result.ml_score;
  ruleVal.textContent = result.rule_score;

  ringVisual.className = `ring-visual ${result.is_spam ? "result-spam" : "result-safe"}`;
  ringLabel.textContent = result.is_spam ? "Spam blocked" : "Call genuine";

  verdictCard.className = `verdict-card ${result.is_spam ? "spam" : "safe"}`;
  verdictLabel.textContent = result.is_spam
    ? `Spam detected (${result.primary_category || "unknown"})`
    : "Looks like a genuine call";
  const transcriptNote = result.transcript ? `Heard: "${result.transcript}"\n\n` : "";
  verdictReasons.textContent = transcriptNote + (result.reasons.length
    ? result.reasons.join("\n")
    : "No rule matches — decision based on ML model only.");

  await playIvr(result.ivr_conversation);
  addHistoryItem(result);
}

function resetVisualsForAnalyzing() {
  ringVisual.className = "ring-visual analyzing";
  ringLabel.textContent = "Analyzing…";
  setGauge(0, "#6C8CFF");
  mlBar.style.width = "0%";
  ruleBar.style.width = "0%";
  mlVal.textContent = "--";
  ruleVal.textContent = "--";
  verdictCard.className = "verdict-card";
  verdictLabel.textContent = "Screening call…";
  verdictReasons.textContent = "";
  ivrTranscript.innerHTML = '<p class="ivr-placeholder">Listening to caller and running detection…</p>';
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  answerBtn.disabled = true;
  answerBtn.textContent = "Screening…";
  resetVisualsForAnalyzing();

  const payload = {
    phone_number: document.getElementById("phoneNumber").value.trim(),
    transcript: document.getElementById("transcript").value.trim(),
    calls_per_day: document.getElementById("callsPerDay").value,
    avg_call_duration: document.getElementById("avgDuration").value,
    is_international: document.getElementById("isInternational").checked,
  };

  try {
    const res = await fetch("/api/simulate_call", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();

    if (!res.ok) {
      verdictLabel.textContent = result.error || "Something went wrong";
      return;
    }

    await sleep(700); // let the "analyzing" animation breathe
    await renderResult(result);
  } catch (err) {
    verdictLabel.textContent = "Error reaching the detection server";
    console.error(err);
  } finally {
    answerBtn.disabled = false;
    answerBtn.textContent = "Answer with AI";
  }
});

// ---------- AUDIO UPLOAD: auto-transcribe + auto-analyze, no typing needed ----------
const dropzone = document.getElementById("uploadDropzone");
const audioFileInput = document.getElementById("audioFileInput");
const uploadStatus = document.getElementById("uploadStatus");

dropzone.addEventListener("click", () => audioFileInput.click());

["dragover", "dragenter"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("drag-over"); })
);
dropzone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) {
    audioFileInput.files = e.dataTransfer.files;
    handleAudioUpload(e.dataTransfer.files[0]);
  }
});
audioFileInput.addEventListener("change", () => {
  if (audioFileInput.files.length) handleAudioUpload(audioFileInput.files[0]);
});

async function handleAudioUpload(file) {
  uploadStatus.classList.remove("error");
  uploadStatus.textContent = `Transcribing "${file.name}"…`;
  resetVisualsForAnalyzing();
  ringLabel.textContent = "Listening…";

  const formData = new FormData();
  formData.append("audio", file);
  formData.append("phone_number", document.getElementById("phoneNumber").value.trim() || "Unknown (from recording)");
  formData.append("calls_per_day", document.getElementById("callsPerDay").value || 1);
  formData.append("avg_call_duration", document.getElementById("avgDuration").value || 60);
  formData.append("is_international", document.getElementById("isInternational").checked);

  try {
    const res = await fetch("/api/analyze_audio", { method: "POST", body: formData });
    const result = await res.json();

    if (!res.ok) {
      uploadStatus.classList.add("error");
      uploadStatus.textContent = result.error || "Couldn't analyze that recording";
      ringLabel.textContent = "Ready";
      ringVisual.className = "ring-visual";
      return;
    }

    uploadStatus.textContent = "Transcribed and analyzed automatically ✓";
    document.getElementById("transcript").value = result.transcript;
    await renderResult(result);
  } catch (err) {
    uploadStatus.classList.add("error");
    uploadStatus.textContent = "Error reaching the detection server";
    console.error(err);
  } finally {
    audioFileInput.value = "";
  }
}

// Load recent history on page load
(async function loadHistory() {
  try {
    const res = await fetch("/api/call_log");
    const rows = await res.json();
    rows.forEach(addHistoryItem);
  } catch (e) { /* no history yet */ }
})();

// Clear history button
document.getElementById("clearHistoryBtn").addEventListener("click", async () => {
  const confirmed = confirm("Clear all call history? This can't be undone.");
  if (!confirmed) return;
  try {
    await fetch("/api/call_log", { method: "DELETE" });
    callHistory.innerHTML = "";
  } catch (e) {
    console.error("Failed to clear history", e);
  }
});
