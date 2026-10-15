"use strict";

const LANGUAGE_TEXT = {
  ta: { greeting: "வணக்கம். அரசு திட்டங்களைப் பற்றி என்னிடம் கேளுங்கள்.", speak: "பேச தொடவும்", ask: "கேளுங்கள்", listening: "கேட்கிறேன்…", thinking: "தேடுகிறேன்…", speaking: "பேசுகிறேன்…", ready: "தயார்", error: "மன்னிக்கவும். மீண்டும் முயற்சிக்கவும்.", language: "மொழி", reset: "மீண்டும் தொடங்கு", type: "அல்லது உங்கள் கேள்வியை எழுதுங்கள்", browse: "எந்த உதவி தேவை?", categories: ["விவசாயிகள்", "பெண்கள்", "மாணவர்கள்", "சுகாதாரம்", "வீடு", "ஓய்வூதியம்", "வேலை"], result: "திட்ட விவரம்", read: "சத்தமாக வாசிக்கவும்" },
  ml: { greeting: "നമസ്കാരം. സർക്കാർ പദ്ധതികളെക്കുറിച്ച് എന്നോട് ചോദിക്കൂ.", speak: "സംസാരിക്കാൻ തൊടുക", ask: "ചോദിക്കുക", listening: "കേൾക്കുന്നു…", thinking: "തിരയുന്നു…", speaking: "സംസാരിക്കുന്നു…", ready: "തയ്യാർ", error: "ക്ഷമിക്കണം. വീണ്ടും ശ്രമിക്കുക.", language: "ഭാഷ", reset: "പുതുതായി തുടങ്ങുക", type: "അല്ലെങ്കിൽ ചോദ്യം ടൈപ്പ് ചെയ്യുക", browse: "എന്താണ് വേണ്ടത്?", categories: ["കർഷകർ", "സ്ത്രീകൾ", "വിദ്യാർത്ഥികൾ", "ആരോഗ്യം", "ഭവനം", "പെൻഷൻ", "തൊഴിൽ"], result: "പദ്ധതി വിവരങ്ങൾ", read: "വായിക്കുക" },
  kn: { greeting: "ನಮಸ್ಕಾರ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ನನ್ನನ್ನು ಕೇಳಿ.", speak: "ಮಾತನಾಡಲು ಸ್ಪರ್ಶಿಸಿ", ask: "ಕೇಳಿ", listening: "ಕೇಳುತ್ತಿದೆ…", thinking: "ಹುಡುಕುತ್ತಿದೆ…", speaking: "ಮಾತನಾಡುತ್ತಿದೆ…", ready: "ಸಿದ್ಧ", error: "ಕ್ಷಮಿಸಿ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.", language: "ಭಾಷೆ", reset: "ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ", type: "ಅಥವಾ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ", browse: "ನಿಮಗೆ ಯಾವ ಸಹಾಯ ಬೇಕು?", categories: ["ರೈತರು", "ಮಹಿಳೆಯರು", "ವಿದ್ಯಾರ್ಥಿಗಳು", "ಆರೋಗ್ಯ", "ವಸತಿ", "ಪಿಂಚಣಿ", "ಉದ್ಯೋಗ"], result: "ಯೋಜನೆಯ ಮಾಹಿತಿ", read: "ಓದಿ ಕೇಳಿಸಿ" },
  te: { greeting: "నమస్కారం. ప్రభుత్వ పథకాల గురించి నన్ను అడగండి.", speak: "మాట్లాడటానికి తాకండి", ask: "అడగండి", listening: "వింటున్నాను…", thinking: "వెతుకుతున్నాను…", speaking: "మాట్లాడుతున్నాను…", ready: "సిద్ధం", error: "క్షమించండి. మళ్లీ ప్రయత్నించండి.", language: "భాష", reset: "మళ్లీ ప్రారంభించండి", type: "లేదా మీ ప్రశ్నను టైప్ చేయండి", browse: "మీకు ఏ సహాయం కావాలి?", categories: ["రైతులు", "మహిళలు", "విద్యార్థులు", "ఆరోగ్యం", "గృహనిర్మాణం", "పెన్షన్", "ఉపాధి"], result: "పథకం వివరాలు", read: "చదివి వినిపించండి" },
  hi: { greeting: "नमस्ते। सरकारी योजनाओं के बारे में मुझसे पूछें।", speak: "बोलने के लिए छुएँ", ask: "पूछें", listening: "सुन रहा है…", thinking: "खोज रहा है…", speaking: "बोल रहा है…", ready: "तैयार", error: "क्षमा करें। फिर से कोशिश करें।", language: "भाषा", reset: "फिर से शुरू करें", type: "या अपना सवाल लिखें", browse: "आपको किस चीज़ में मदद चाहिए?", categories: ["किसान", "महिलाएँ", "विद्यार्थी", "स्वास्थ्य", "आवास", "पेंशन", "रोज़गार"], result: "योजना की जानकारी", read: "ज़ोर से सुनें" },
  mr: { greeting: "नमस्कार. सरकारी योजनांबद्दल मला विचारा.", speak: "बोलण्यासाठी स्पर्श करा", ask: "विचारा", listening: "ऐकत आहे…", thinking: "शोधत आहे…", speaking: "बोलत आहे…", ready: "तयार", error: "क्षमस्व. पुन्हा प्रयत्न करा.", language: "भाषा", reset: "पुन्हा सुरू करा", type: "किंवा तुमचा प्रश्न लिहा", browse: "तुम्हाला कशासाठी मदत हवी आहे?", categories: ["शेतकरी", "महिला", "विद्यार्थी", "आरोग्य", "घरकुल", "निवृत्ती", "रोजगार"], result: "योजनेची माहिती", read: "मोठ्याने ऐका" },
  en: { greeting: "Welcome. Ask me about government schemes.", speak: "Tap to speak", ask: "Ask", listening: "Listening…", thinking: "Looking for information…", speaking: "Speaking…", ready: "Ready", error: "Sorry. Please try again.", language: "Language", reset: "Start over", type: "Or type your question", browse: "What are you looking for?", categories: ["Farmers", "Women", "Students", "Health", "Housing", "Pensions", "Employment"], result: "Scheme information", read: "🔊 Read aloud" }
};

const CATEGORIES = ["farmers", "women", "students", "health", "housing", "pensions", "employment"];
const CATEGORY_ICONS = ["🌾", "👩", "🎓", "🩺", "🏠", "🧓", "🧰"];
const LANGUAGES = [
  { code: "ta", label: "தமிழ்", icon: "🪷" },
  { code: "ml", label: "മലയാളം", icon: "🌴" },
  { code: "kn", label: "ಕನ್ನಡ", icon: "🌾" },
  { code: "te", label: "తెలుగు", icon: "🌻" },
  { code: "hi", label: "हिन्दी", icon: "🪔" },
  { code: "mr", label: "मराठी", icon: "🚜" },
  { code: "en", label: "English", icon: "🌐" }
];

const state = { language: null, category: null, busy: false, stream: null, context: null, processor: null, source: null, silentGain: null, audio: [], preRoll: [], speaking: false, silenceMs: 0, lastActivity: Date.now(), idleTimeoutMs: 90000, timer: null };
const $ = (id) => document.getElementById(id);
const home = $("home");
const kiosk = $("kiosk");
const langGrid = $("language-grid");
const speechButton = $("speak-button");
const waveform = $("waveform");
const waveContext = waveform.getContext("2d");
const audioPlayer = $("audio-player");

function text() { return LANGUAGE_TEXT[state.language] || LANGUAGE_TEXT.en; }
function activity() { state.lastActivity = Date.now(); }
function setStatus(key) { $("voice-state").textContent = text()[key] || key; activity(); }

async function api(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", ...options });
  const value = await response.json();
  if (!response.ok) {
    if (value.audio_base64) playAudio(value);
    throw new Error(value.detail || text().error);
  }
  return value;
}

function stopAudio() {
  audioPlayer.pause();
  audioPlayer.removeAttribute("src");
  audioPlayer.load();
}

function selectLanguage(language) {
  state.language = language;
  state.category = null;
  home.classList.add("hidden");
  kiosk.classList.remove("hidden");
  document.documentElement.lang = language;
  $("welcome-title").textContent = text().result;
  $("greeting").textContent = text().greeting;
  $("change-language").querySelector("span").textContent = text().language;
  $("reset-button").textContent = text().reset;
  $("speak-label").textContent = text().speak;
  $("question-form").querySelector("label").textContent = text().type;
  $("send-button").textContent = text().ask;
  $("browse-title").textContent = text().browse;
  $("result-title").textContent = text().result;
  $("read-button").textContent = text().read;
  renderCategories();
  if (!responseHasAudio) setStatus("ready");
  activity();
  api(`/api/greeting?language=${encodeURIComponent(language)}`).then(playAudio).catch(() => {});
}

function renderLanguages() {
  for (const language of LANGUAGES) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "language-card";
    button.innerHTML = `<span class="icon" aria-hidden="true">${language.icon}</span>${language.label}`;
    button.addEventListener("click", () => selectLanguage(language.code));
    langGrid.append(button);
  }
}

function renderCategories() {
  const grid = $("category-grid");
  grid.replaceChildren();
  CATEGORIES.forEach((category, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category-button";
    button.innerHTML = `<span class="icon" aria-hidden="true">${CATEGORY_ICONS[index]}</span>${text().categories[index]}`;
    button.addEventListener("click", () => browse(category));
    grid.append(button);
  });
}

function playAudio(response) {
  if (!response) return;
  if (!response.audio_base64) {
    setStatus("ready");
    return;
  }
  audioPlayer.src = `data:audio/wav;base64,${response.audio_base64}`;
  setStatus("speaking");
  audioPlayer.play().catch(() => setStatus("ready"));
}

function showResult(result) {
  $("result-panel").classList.remove("hidden");
  $("result-title").textContent = text().result;
  $("reply").textContent = result.reply || text().error;
  $("transcript").textContent = result.transcript ? `You said: ${result.transcript}` : "";
  $("offline-note").classList.toggle("hidden", !result.offline);
  $("offline-note").textContent = result.offline ? "Using available scheme records without the online answer service." : "";
  const list = $("scheme-list");
  list.replaceChildren();
  const schemes = result.answer
    ? [...(result.answer.schemes || []), ...(result.answer.related_schemes || [])]
    : [];
  for (const scheme of schemes) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "scheme-card";
    const title = document.createElement("span");
    title.textContent = scheme.title;
    const note = document.createElement("small");
    note.textContent = scheme.development_sample ? "Development sample — not official scheme data" : "Tap for details and read-aloud";
    card.append(title, note);
    card.addEventListener("click", async () => {
      try {
        setStatus("thinking");
        const detail = await api(`/api/schemes/${encodeURIComponent(scheme.scheme_id)}?language=${encodeURIComponent(state.language)}`);
        $("reply").textContent = detail.reply;
        playAudio(detail);
      } catch (error) {
        showError(error);
      }
    });
    list.append(card);
  }
  $("read-button").classList.remove("hidden");
  $("read-button").onclick = () => playAudio(result);
  $("result-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  activity();
}

function showError(error) {
  $("result-panel").classList.remove("hidden");
  $("reply").textContent = text().error;
  $("scheme-list").replaceChildren();
  setStatus("ready");
}

async function ask(question) {
  if (state.busy || !question.trim()) return;
  state.busy = true;
  let responseHasAudio = false;
  activity();
  setStatus("thinking");
  $("send-button").disabled = true;
  speechButton.disabled = true;
  try {
    const result = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: question.trim(), language: state.language, category: state.category })
    });
    responseHasAudio = Boolean(result.audio_base64);
    showResult(result);
    playAudio(result);
  } catch (error) {
    showError(error);
  } finally {
    $("send-button").disabled = false;
    speechButton.disabled = false;
    state.busy = false;
    if (!responseHasAudio) setStatus("ready");
  }
}

async function browse(category) {
  state.category = category;
  setStatus("thinking");
  try {
    const result = await api("/api/browse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category, language: state.language })
    });
    showResult(result);
    playAudio(result);
  } catch (error) {
    showError(error);
  }
}

function drawWave(level) {
  const width = waveform.width;
  const height = waveform.height;
  waveContext.clearRect(0, 0, width, height);
  waveContext.fillStyle = "#1b7753";
  const barWidth = 8;
  const gap = 7;
  for (let x = 0; x < width; x += barWidth + gap) {
    const variation = 0.35 + Math.abs(Math.sin(x * 0.052 + Date.now() / 200)) * 0.65;
    const barHeight = Math.max(3, Math.min(height - 8, level * height * variation * 5));
    waveContext.fillRect(x, (height - barHeight) / 2, barWidth, barHeight);
  }
}

function rms(samples) {
  let sum = 0;
  for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
  return Math.sqrt(sum / samples.length);
}

function resample(samples, fromRate, toRate) {
  if (fromRate === toRate) return samples;
  const outputLength = Math.round(samples.length * toRate / fromRate);
  const output = new Float32Array(outputLength);
  const ratio = fromRate / toRate;
  for (let i = 0; i < outputLength; i++) {
    const position = i * ratio;
    const before = Math.floor(position);
    const after = Math.min(before + 1, samples.length - 1);
    const weight = position - before;
    output[i] = samples[before] * (1 - weight) + samples[after] * weight;
  }
  return output;
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const write = (offset, value) => { for (let i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i)); };
  write(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  write(8, "WAVE");
  write(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  write(36, "data");
  view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, sample < 0 ? sample * 32768 : sample * 32767, true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}

function toBase64(blob) {
  return blob.arrayBuffer().then((buffer) => {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    const chunkSize = 0x8000;
    for (let index = 0; index < bytes.length; index += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
    }
    return btoa(binary);
  });
}

function cleanupMicrophone() {
  if (state.processor) state.processor.disconnect();
  if (state.silentGain) state.silentGain.disconnect();
  if (state.source) state.source.disconnect();
  if (state.stream) state.stream.getTracks().forEach((track) => track.stop());
  if (state.context) state.context.close().catch(() => {});
  state.processor = null;
  state.silentGain = null;
  state.source = null;
  state.stream = null;
  state.context = null;
}

async function stopRecording() {
  if (!state.context) return;
  cleanupMicrophone();
  speechButton.setAttribute("aria-pressed", "false");
  speechButton.disabled = true;
  drawWave(0);
  if (!state.audio.length) {
    setStatus("ready");
    speechButton.disabled = false;
    return;
  }
  const chunks = state.audio.splice(0).concat(state.preRoll.splice(0));
  let sampleCount = 0;
  chunks.forEach((chunk) => { sampleCount += chunk.length; });
  const combined = new Float32Array(sampleCount);
  let offset = 0;
  chunks.forEach((chunk) => { combined.set(chunk, offset); offset += chunk.length; });
  setStatus("thinking");
  let responseHasAudio = false;
  try {
    const wav = encodeWav(resample(combined, state.sampleRate, 16000), 16000);
    const requestBody = {
      audio_base64: await toBase64(wav),
      language: state.language,
      category: state.category
    };
    const result = await api("/api/chat/voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody)
    });
    responseHasAudio = Boolean(result.audio_base64);
    showResult(result);
    playAudio(result);
  } catch (error) {
    showError(error);
  } finally {
    speechButton.disabled = false;
    if (!responseHasAudio) setStatus("ready");
    activity();
  }
}

async function startRecording() {
  activity();
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true }, video: false });
    state.context = new AudioContext();
    state.sampleRate = state.context.sampleRate;
    state.source = state.context.createMediaStreamSource(state.stream);
    state.processor = state.context.createScriptProcessor(4096, 1, 1);
    state.silentGain = state.context.createGain();
    state.silentGain.gain.value = 0;
    state.audio = [];
    state.preRoll = [];
    state.speaking = false;
    state.silenceMs = 0;
    speechButton.setAttribute("aria-pressed", "true");
    setStatus("listening");
    state.source.connect(state.processor);
    state.processor.connect(state.silentGain);
    state.silentGain.connect(state.context.destination);
    state.processor.onaudioprocess = (event) => {
      const samples = new Float32Array(event.inputBuffer.getChannelData(0));
      const volume = rms(samples);
      drawWave(volume);
      if (!state.speaking) {
        state.preRoll.push(samples);
        if (state.preRoll.length > 5) state.preRoll.shift();
        if (volume > 0.018) {
          state.speaking = true;
          state.audio.push(...state.preRoll.splice(0));
        }
      } else {
        state.audio.push(samples);
        state.silenceMs = volume < 0.011 ? state.silenceMs + samples.length / state.sampleRate * 1000 : 0;
        if (state.silenceMs >= 1000 || state.audio.length * 4096 / state.sampleRate >= 15) stopRecording();
      }
    };
  } catch (_) {
    cleanupMicrophone();
    setStatus("ready");
    showError(new Error(`${text().error} Please type your question or ask kiosk staff.`));
  }
}

function resetKiosk() {
  stopAudio();
  cleanupMicrophone();
  state.language = null;
  state.category = null;
  state.audio = [];
  state.preRoll = [];
  state.busy = false;
  $("question").value = "";
  $("reply").textContent = "";
  $("transcript").textContent = "";
  $("scheme-list").replaceChildren();
  $("result-panel").classList.add("hidden");
  $("offline-note").classList.add("hidden");
  kiosk.classList.add("hidden");
  home.classList.remove("hidden");
  activity();
}

function checkIdle() {
  if (state.language && Date.now() - state.lastActivity > state.idleTimeoutMs) resetKiosk();
}

renderLanguages();
api("/api/config").then((config) => {
  if (Number.isFinite(config.idle_timeout_seconds) && config.idle_timeout_seconds > 0) {
    state.idleTimeoutMs = config.idle_timeout_seconds * 1000;
  }
}).catch(() => {});
$("question-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const value = $("question").value;
  $("question").value = "";
  ask(value);
});
speechButton.addEventListener("click", () => state.context ? stopRecording() : startRecording());
$("change-language").addEventListener("click", resetKiosk);
$("reset-button").addEventListener("click", resetKiosk);
audioPlayer.addEventListener("ended", () => setStatus("ready"));
audioPlayer.addEventListener("error", () => setStatus("ready"));
document.addEventListener("pointerdown", activity, { passive: true });
document.addEventListener("keydown", activity);
state.timer = window.setInterval(checkIdle, 1000);
