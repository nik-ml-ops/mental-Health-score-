(() => {
  "use strict";

  const API_BASE = "http://127.0.0.1:2200";

  const form = document.getElementById("predict-form");
  const submitBtn = document.getElementById("submit-btn");
  const resetBtn = document.getElementById("reset-btn");
  const errorRetryBtn = document.getElementById("error-retry-btn");

  const stateIdle = document.getElementById("state-idle");
  const stateLoading = document.getElementById("state-loading");
  const stateResult = document.getElementById("state-result");
  const stateError = document.getElementById("state-error");

  const scoreNumberEl = document.getElementById("score-number");
  const scoreBandEl = document.getElementById("score-band");
  const scoreContextEl = document.getElementById("score-context");
  const gaugeFill = document.getElementById("gauge-fill");
  const errorLabelEl = document.getElementById("error-label");
  const errorCopyEl = document.getElementById("error-copy");

  const GAUGE_ARC_LENGTH = 314; // approx pi * r(100)

  // ---------------------------------------------------------
  // Draw tick marks on both gauges (0..10, every 2 units)
  // ---------------------------------------------------------
  function drawTicks() {
    document.querySelectorAll(".gauge-ticks").forEach((g) => {
      g.innerHTML = "";
      const cx = 120, cy = 140, rOuter = 100, rInner = 90;
      for (let i = 0; i <= 10; i += 2) {
        const angle = Math.PI - (i / 10) * Math.PI; // 180deg -> 0deg
        const x1 = cx + rOuter * Math.cos(angle);
        const y1 = cy - rOuter * Math.sin(angle);
        const x2 = cx + rInner * Math.cos(angle);
        const y2 = cy - rInner * Math.sin(angle);
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line"); // ✅ fixed namespace
        line.setAttribute("x1", x1.toFixed(1));
        line.setAttribute("y1", y1.toFixed(1));
        line.setAttribute("x2", x2.toFixed(1));
        line.setAttribute("y2", y2.toFixed(1));
        g.appendChild(line);
      }
    });
  }
  drawTicks();

  // ---------------------------------------------------------
  // Segmented control (stress_level) wiring
  // ---------------------------------------------------------
  const segGroup = document.getElementById("stress_level_group");
  const stressHiddenInput = document.getElementById("stress_level");
  if (segGroup && stressHiddenInput) {
    segGroup.querySelectorAll(".seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        segGroup.querySelectorAll(".seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        stressHiddenInput.value = btn.dataset.value;
        clearFieldError(stressHiddenInput);
      });
    });
  }

  // ---------------------------------------------------------
  // Field-level error helpers
  // ---------------------------------------------------------
  function fieldWrapper(input) {
    return input ? input.closest(".field") : null;
  }

  function setFieldError(input, message) {
    const wrap = fieldWrapper(input);
    if (!wrap) return;
    wrap.classList.add("field-error");
    const msgEl = wrap.querySelector(".error-msg");
    if (msgEl) msgEl.textContent = message;
  }

  function clearFieldError(input) {
    const wrap = fieldWrapper(input);
    if (!wrap) return;
    wrap.classList.remove("field-error");
    const msgEl = wrap.querySelector(".error-msg");
    if (msgEl) msgEl.textContent = "";
  }

  function clearAllErrors() {
    form.querySelectorAll(".field").forEach((f) => f.classList.remove("field-error"));
    form.querySelectorAll(".error-msg").forEach((m) => (m.textContent = ""));
  }

  // ---------------------------------------------------------
  // Helper function to capitalize words to match FastAPI Literals
  // ---------------------------------------------------------
  function toTitleCase(str) {
    if (!str) return "";
    return str.split(' ').map(word => {
      if (word.toLowerCase() === 'usa') return 'USA';
      if (word.toLowerCase() === 'uk') return 'UK';
      if (word.toLowerCase() === 'tiktok') return 'TikTok';
      if (word.toLowerCase() === 'youtube') return 'YouTube';
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    }).join(' ');
  }

  // ---------------------------------------------------------
  // Client-side validation mirroring the StudentData model
  // ---------------------------------------------------------
  function validate(payload) {
    const errors = [];

    const numericChecks = [
      ["age", 10, 100, "Age"],
      ["avg_daily_usage_hours", 0, 24, "Avg_Daily_Usage_Hours"],
      ["daily_unlocks", 0, Infinity, "Daily_Unlocks"],
      ["study_hours", 0, 24, "Study_Hours"],
      ["physical_activity_hours", 0, 24, "Physical_Activity_Hours"],
      ["sleep_hours_per_night", 0, 24, "Sleep_Hours_Per_Night"],
    ];

    numericChecks.forEach(([domId, min, max, payloadKey]) => {
      const input = document.getElementById(domId);
      const val = payload[payloadKey];
      if (val === "" || val === null || Number.isNaN(val)) {
        errors.push([input, "This field is required."]);
      } else if (val < min || val > max) {
        errors.push([input, `Must be between ${min} and ${max === Infinity ? "0+" : max}.`]);
      }
    });

    const stringChecks = [
      ["gender", "Gender"],
      ["country", "Country"],
      ["academic_level", "Academic_Level"],
      ["most_used_platform", "Most_Used_Platform"],
      ["purpose_of_use", "Purpose_Of_Use"]
    ];

    stringChecks.forEach(([domId, payloadKey]) => {
      const input = document.getElementById(domId);
      if (!payload[payloadKey] || String(payload[payloadKey]).trim() === "") {
        errors.push([input, "This field is required."]);
      }
    });

    if (!payload.Stress_Level) {
      errors.push([stressHiddenInput, "Pick a stress level."]);
    }

    return errors;
  }

  // ---------------------------------------------------------
  // Gather form data into the exact StudentData shape (PascalCase)
  // ---------------------------------------------------------
  function collectPayload() {
    const fd = new FormData(form);
    const payload = {
      Age: fd.get("age") === "" ? NaN : parseInt(fd.get("age"), 10),
      Gender: toTitleCase(fd.get("gender") || ""),
      Country: toTitleCase((fd.get("country") || "").trim()),
      Academic_Level: toTitleCase(fd.get("academic_level") || ""),
      Most_Used_Platform: toTitleCase(fd.get("most_used_platform") || ""),
      Purpose_Of_Use: toTitleCase(fd.get("purpose_of_use") || ""),
      Avg_Daily_Usage_Hours: fd.get("avg_daily_usage_hours") === "" ? NaN : parseFloat(fd.get("avg_daily_usage_hours")),
      Daily_Unlocks: fd.get("daily_unlocks") === "" ? NaN : parseInt(fd.get("daily_unlocks"), 10),
      Study_Hours: fd.get("study_hours") === "" ? NaN : parseFloat(fd.get("study_hours")),
      Physical_Activity_Hours: fd.get("physical_activity_hours") === "" ? NaN : parseFloat(fd.get("physical_activity_hours")),
      Sleep_Hours_Per_Night: fd.get("sleep_hours_per_night") === "" ? NaN : parseFloat(fd.get("sleep_hours_per_night")),
      Stress_Level: toTitleCase(fd.get("stress_level") || ""),
    };
    console.log("payload", payload);
    return payload;
  }

  // ---------------------------------------------------------
  // UI state switching
  // ---------------------------------------------------------
  function showState(name) {
    [stateIdle, stateLoading, stateResult, stateError].forEach((el) => { if(el) el.hidden = true; });
    const targets = { idle: stateIdle, loading: stateLoading, result: stateResult, error: stateError };
    if (targets[name]) targets[name].hidden = false;
  }

  function setSubmitting(isSubmitting) {
    if (!submitBtn) return;
    submitBtn.disabled = isSubmitting;
    submitBtn.classList.toggle("loading", isSubmitting);
  }

  function bandFor(score) {
    if (score < 4) {
      return {
        label: "Signal: strained",
        context: "Your responses suggest elevated strain right now. Small shifts in sleep or screen time can go a long way.",
      };
    }
    if (score < 7) {
      return {
        label: "Signal: balanced",
        context: "Your rhythm looks fairly steady, with some room to recover",
      };
    }
  }
  // ---------------------------------------------------------
  // Submit prediction request to local API
  // ---------------------------------------------------------
  async function submitPrediction(payload) {
    const response = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      mode: "cors",
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || "Prediction failed.");
    }

    return response.json();
  }

  function signalColorFor(score) {
    const normalized = Math.max(0, Math.min(10, Number(score) || 0));
    if (normalized < 4) return "#D9534F";
    if (normalized < 7) return "#E3B341";
    return "#4C9A78";
  }

  function renderResult(result) {
    if (!scoreNumberEl || !scoreBandEl || !scoreContextEl || !gaugeFill) return;

    const score = Number(result.score || 0);
    const panel = document.querySelector(".result-panel");
    const accent = signalColorFor(score);

    scoreNumberEl.textContent = score.toFixed(1);
    const band = result.band || "balanced";
    const labels = {
      strained: "Signal: strained",
      balanced: "Signal: balanced",
      resilient: "Signal: resilient",
    };
    const contexts = {
      strained: "Your inputs suggest elevated strain right now. Small shifts in sleep or screen time can make a meaningful difference.",
      balanced: "Your rhythm looks fairly steady, with some room to recover and maintain momentum.",
      resilient: "Your current habits look strong, and your routine appears resilient overall.",
    };
    scoreBandEl.textContent = labels[band] || labels.balanced;
    scoreContextEl.textContent = contexts[band] || contexts.balanced;
    const pct = Math.max(0, Math.min(100, (score / 10) * 100));
    gaugeFill.style.setProperty("stroke-dashoffset", `${314 - (314 * pct) / 100}`);
    if (panel) panel.style.setProperty("--signal-accent", accent);
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAllErrors();
    showState("loading");
    setSubmitting(true);

    const payload = collectPayload();
    const errors = validate(payload);
    if (errors.length) {
      errors.forEach(([input, message]) => setFieldError(input, message));
      showState("idle");
      setSubmitting(false);
      return;
    }

    try {
      const result = await submitPrediction(payload);
      renderResult(result);
      showState("result");
    } catch (error) {
      errorLabelEl.textContent = "Prediction unavailable";
      errorCopyEl.textContent = error.message || "Please try again in a moment.";
      showState("error");
    } finally {
      setSubmitting(false);
    }
  });

  resetBtn?.addEventListener("click", () => {
    form.reset();
    clearAllErrors();
    showState("idle");
    if (stressHiddenInput) stressHiddenInput.value = "";
    document.querySelectorAll(".seg-btn").forEach((btn) => btn.classList.remove("active"));
  });

})();