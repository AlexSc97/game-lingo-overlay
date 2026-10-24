// Game Lingo Overlay - Frontend Logic

let ws = null;
let currentConfig = {
  region: { left: 400, top: 700, width: 1120, height: 260 },
  theme: "void",
  auto_detect: false,
  overlay_opacity: 0.92,
  font_size: 18
};

let currentActiveWord = null;
let tooltipHideTimeout = null;

// DOM Elements
const tokensContainer = document.getElementById("tokensContainer");
const translationBox = document.getElementById("translationBox");
const fullTranslationText = document.getElementById("fullTranslationText");
const btnToggleReveal = document.getElementById("btnToggleReveal");
const revealLabel = document.getElementById("revealLabel");
const wordTooltip = document.getElementById("wordTooltip");
const tooltipWord = document.getElementById("tooltipWord");
const tooltipTranslation = document.getElementById("tooltipTranslation");
const btnTts = document.getElementById("btnTts");
const btnSaveWord = document.getElementById("btnSaveWord");
const statusDot = document.querySelector(".status-dot");
const statusText = document.querySelector(".status-text");
const btnCapture = document.getElementById("btnCapture");
const btnAutoToggle = document.getElementById("btnAutoToggle");
const autoStatus = document.getElementById("autoStatus");
const btnSettings = document.getElementById("btnSettings");
const btnLexicon = document.getElementById("btnLexicon");
const settingsModal = document.getElementById("settingsModal");
const lexiconModal = document.getElementById("lexiconModal");
const btnCloseSettings = document.getElementById("btnCloseSettings");
const btnCloseLexicon = document.getElementById("btnCloseLexicon");
const btnSaveSettings = document.getElementById("btnSaveSettings");
const themeBadge = document.getElementById("themeBadge");

// Region Inputs
const inputLeft = document.getElementById("inputLeft");
const inputTop = document.getElementById("inputTop");
const inputWidth = document.getElementById("inputWidth");
const inputHeight = document.getElementById("inputHeight");
const inputOpacity = document.getElementById("inputOpacity");
const opacityValue = document.getElementById("opacityValue");

// --- WebSocket Connection ---
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host || "127.0.0.1:8000";
  const wsUrl = `${protocol}//${host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    statusDot.classList.remove("offline");
    statusText.textContent = "Conectado";
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "init" || data.type === "config_update") {
        applyConfig(data.config);
      } else if (data.type === "translation_update") {
        handleTranslationUpdate(data.payload);
      }
    } catch (e) {
      console.error("[WS] Error parsing message:", e);
    }
  };

  ws.onclose = () => {
    statusDot.classList.add("offline");
    statusText.textContent = "Desconectado (Reconectando...)";
    setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = () => {
    ws.close();
  };
}

// --- Configuration & Themes ---
function applyConfig(cfg) {
  if (!cfg) return;
  currentConfig = { ...currentConfig, ...cfg };

  // Set inputs
  if (cfg.region) {
    inputLeft.value = cfg.region.left;
    inputTop.value = cfg.region.top;
    inputWidth.value = cfg.region.width;
    inputHeight.value = cfg.region.height;
  }

  // Theme
  document.body.className = `theme-${cfg.theme || "void"}`;
  themeBadge.textContent = (cfg.theme || "VOID").toUpperCase();
  document.querySelectorAll(".theme-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.theme === cfg.theme);
  });

  // Auto detect
  autoStatus.textContent = cfg.auto_detect ? "ON" : "OFF";
  btnAutoToggle.classList.toggle("btn-primary", cfg.auto_detect);

  // Opacity
  if (cfg.overlay_opacity) {
    const pct = Math.round(cfg.overlay_opacity * 100);
    inputOpacity.value = pct;
    opacityValue.textContent = `${pct}%`;
    document.getElementById("overlayContainer").style.opacity = cfg.overlay_opacity;
  }
}

// --- Render Interactive Dialogue & Words ---
function handleTranslationUpdate(payload) {
  if (!payload || payload.status === "empty") {
    tokensContainer.innerHTML = `<span class="placeholder-text">⚠️ No se detectó texto en la zona de diálogo. Revisa la región en ⚙️.</span>`;
    fullTranslationText.textContent = "No hay traducción disponible.";
    return;
  }

  const analysis = payload.analysis;
  if (!analysis) return;

  // 1. Render Interactive Tokens
  tokensContainer.innerHTML = "";
  analysis.tokens.forEach((token) => {
    if (token.is_word) {
      const span = document.createElement("span");
      span.className = "token-word";
      span.textContent = token.raw;
      span.dataset.clean = token.clean;
      span.dataset.trans = token.translation || token.clean;

      span.addEventListener("mouseenter", (e) => showTooltip(e.target));
      span.addEventListener("mouseleave", () => scheduleHideTooltip());
      span.addEventListener("click", (e) => {
        showTooltip(e.target);
        speakWord(token.clean);
      });

      tokensContainer.appendChild(span);
    } else {
      // Space or punctuation
      const textNode = document.createTextNode(token.raw);
      tokensContainer.appendChild(textNode);
    }
  });

  // 2. Set Full Translation (Keep blurred for active learning)
  fullTranslationText.textContent = analysis.full_translation || "Traducción completa no disponible.";
  setBlurred(true);
}

// --- Tooltip & Interactive Learning ---
function showTooltip(el) {
  clearTimeout(tooltipHideTimeout);
  currentActiveWord = el;

  document.querySelectorAll(".token-word").forEach(w => w.classList.remove("active-word"));
  el.classList.add("active-word");

  const word = el.dataset.clean;
  const translation = el.dataset.trans;

  tooltipWord.textContent = word;
  tooltipTranslation.textContent = translation;

  // Position tooltip above element
  const rect = el.getBoundingClientRect();
  wordTooltip.style.display = "block";

  const tipWidth = wordTooltip.offsetWidth;
  const tipHeight = wordTooltip.offsetHeight;

  let left = rect.left + (rect.width / 2) - (tipWidth / 2);
  let top = rect.top - tipHeight - 10;

  // Screen boundary guards
  if (left < 10) left = 10;
  if (left + tipWidth > window.innerWidth - 10) left = window.innerWidth - tipWidth - 10;
  if (top < 10) top = rect.bottom + 10; // Flip below if offscreen top

  wordTooltip.style.left = `${left}px`;
  wordTooltip.style.top = `${top}px`;
}

function scheduleHideTooltip() {
  tooltipHideTimeout = setTimeout(() => {
    wordTooltip.style.display = "none";
    if (currentActiveWord) {
      currentActiveWord.classList.remove("active-word");
      currentActiveWord = null;
    }
  }, 250);
}

wordTooltip.addEventListener("mouseenter", () => clearTimeout(tooltipHideTimeout));
wordTooltip.addEventListener("mouseleave", () => scheduleHideTooltip());

// --- Text To Speech (Native Audio Pronunciation) ---
function speakWord(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}

btnTts.addEventListener("click", () => {
  if (tooltipWord.textContent) {
    speakWord(tooltipWord.textContent);
  }
});

// --- Hunter's Lexicon (Save words) ---
btnSaveWord.addEventListener("click", () => {
  const word = tooltipWord.textContent;
  const trans = tooltipTranslation.textContent;
  if (!word) return;

  const saved = JSON.parse(localStorage.getItem("hunter_lexicon") || "{}");
  saved[word] = trans;
  localStorage.setItem("hunter_lexicon", JSON.stringify(saved));

  btnSaveWord.textContent = "✅ Guardada!";
  setTimeout(() => {
    btnSaveWord.textContent = "⭐ Guardar en Lexicon";
  }, 1200);
});

// --- Blur & Reveal Full Translation ---
function setBlurred(blurred) {
  if (blurred) {
    translationBox.classList.add("blurred");
    translationBox.classList.remove("revealed");
    revealLabel.textContent = "Mostrar traducción";
  } else {
    translationBox.classList.remove("blurred");
    translationBox.classList.add("revealed");
    revealLabel.textContent = "Ocultar traducción";
  }
}

translationBox.addEventListener("click", () => {
  const isBlurred = translationBox.classList.contains("blurred");
  setBlurred(!isBlurred);
});

btnToggleReveal.addEventListener("click", () => {
  const isBlurred = translationBox.classList.contains("blurred");
  setBlurred(!isBlurred);
});

// --- Manual Capture Trigger ---
btnCapture.addEventListener("click", () => {
  btnCapture.disabled = true;
  btnCapture.textContent = "⏳ Leyendo...";
  fetch("/api/capture", { method: "POST" })
    .then(r => r.json())
    .catch(err => console.error("Capture failed:", err))
    .finally(() => {
      btnCapture.disabled = false;
      btnCapture.textContent = "📸 Capturar";
    });
});

// --- Auto-Detect Toggle ---
btnAutoToggle.addEventListener("click", () => {
  currentConfig.auto_detect = !currentConfig.auto_detect;
  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(currentConfig)
  }).then(r => r.json()).then(res => applyConfig(res.config));
});

// --- Preset Game Quotes Testing ---
document.querySelectorAll(".preset-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const quote = chip.dataset.quote;
    fetch("/api/analyze-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: quote })
    });
  });
});

// --- Settings & Modal ---
btnSettings.addEventListener("click", () => {
  settingsModal.style.display = "flex";
});

btnCloseSettings.addEventListener("click", () => {
  settingsModal.style.display = "none";
});

// Region Presets for Hollow Knight
document.querySelectorAll(".btn-region-preset").forEach(btn => {
  btn.addEventListener("click", () => {
    const preset = btn.dataset.preset;
    if (preset === "top") {
      inputLeft.value = 450;
      inputTop.value = 140;
      inputWidth.value = 1020;
      inputHeight.value = 220;
    } else if (preset === "bottom") {
      inputLeft.value = 400;
      inputTop.value = 720;
      inputWidth.value = 1120;
      inputHeight.value = 250;
    } else if (preset === "center") {
      inputLeft.value = 350;
      inputTop.value = 420;
      inputWidth.value = 1220;
      inputHeight.value = 280;
    }
  });
});

// Theme Buttons inside modal
document.querySelectorAll(".theme-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    currentConfig.theme = btn.dataset.theme;
    applyConfig(currentConfig);
  });
});

inputOpacity.addEventListener("input", (e) => {
  const val = e.target.value;
  opacityValue.textContent = `${val}%`;
  currentConfig.overlay_opacity = val / 100;
  document.getElementById("overlayContainer").style.opacity = currentConfig.overlay_opacity;
});

btnSaveSettings.addEventListener("click", () => {
  currentConfig.region = {
    left: parseInt(inputLeft.value, 10) || 400,
    top: parseInt(inputTop.value, 10) || 700,
    width: parseInt(inputWidth.value, 10) || 1120,
    height: parseInt(inputHeight.value, 10) || 260
  };
  currentConfig.overlay_opacity = parseInt(inputOpacity.value, 10) / 100;

  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(currentConfig)
  }).then(r => r.json()).then(res => {
    applyConfig(res.config);
    settingsModal.style.display = "none";
  });
});

// --- Hunter's Lexicon Modal ---
btnLexicon.addEventListener("click", () => {
  renderLexicon();
  lexiconModal.style.display = "flex";
});

btnCloseLexicon.addEventListener("click", () => {
  lexiconModal.style.display = "none";
});

function renderLexicon(filterText = "") {
  const saved = JSON.parse(localStorage.getItem("hunter_lexicon") || "{}");
  // Also fetch backend dictionary cache
  fetch("/api/vocab").then(r => r.json()).then(data => {
    const combined = { ...data.words, ...saved };
    const list = document.getElementById("lexiconList");
    const countEl = document.getElementById("lexiconCount");
    list.innerHTML = "";

    const entries = Object.entries(combined).filter(([word, trans]) => {
      const q = filterText.toLowerCase();
      return word.toLowerCase().includes(q) || trans.toLowerCase().includes(q);
    });

    countEl.textContent = entries.length;

    entries.slice(0, 80).forEach(([word, trans]) => {
      const item = document.createElement("div");
      item.className = "lexicon-item";
      item.innerHTML = `<span class="orig">${word}</span><span class="trans">${trans}</span>`;
      item.addEventListener("click", () => speakWord(word));
      list.appendChild(item);
    });
  });
}

document.getElementById("lexiconSearch").addEventListener("input", (e) => {
  renderLexicon(e.target.value);
});

// Close modals when clicking backdrop
window.addEventListener("click", (e) => {
  if (e.target === settingsModal) settingsModal.style.display = "none";
  if (e.target === lexiconModal) lexiconModal.style.display = "none";
});

// --- Keyboard Shortcuts ---
window.addEventListener("keydown", (e) => {
  // If typing in input, ignore shortcuts
  if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;

  if (e.code === "Space") {
    e.preventDefault();
    btnCapture.click();
  } else if (e.code === "KeyR") {
    btnToggleReveal.click();
  } else if (e.code === "Escape") {
    settingsModal.style.display = "none";
    lexiconModal.style.display = "none";
    wordTooltip.style.display = "none";
  }
});

// Start
connectWebSocket();
