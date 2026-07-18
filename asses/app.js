const TONE_NAMES = {
  1: "Tone 1 (high level)",
  2: "Tone 2 (rising)",
  3: "Tone 3 (dipping)",
  4: "Tone 4 (falling)",
};

// When Simple gloss is selected, show a dominant multi-character word instead.
const DOMINANT_WORD_MIN_SHARE = 0.6;
const FREQ_STEPS = 4;

function onsetLabel(onset) {
  return onset === "" ? "∅" : onset;
}

function finalLabel(final) {
  return final;
}

function collectCounts(data) {
  const counts = [];
  for (const tone of Object.values(data.tones)) {
    for (const row of Object.values(tone)) {
      for (const cell of Object.values(row)) {
        if (cell.count > 0) counts.push(cell.count);
      }
    }
  }
  return counts;
}

function frequencyStep(count, logMin, logMax) {
  const log = Math.log(Math.max(count, 1));
  const t =
    logMax === logMin ? 1 : Math.min(1, Math.max(0, (log - logMin) / (logMax - logMin)));
  return Math.min(FREQ_STEPS - 1, Math.floor(t * FREQ_STEPS));
}

function frequencyColors(count, logMin, logMax) {
  const step = frequencyStep(count, logMin, logMax);
  const t = step / (FREQ_STEPS - 1);
  const bgR = Math.round(255 - 210 * t);
  const bgG = Math.round(255 - 55 * t);
  const bgB = Math.round(255 - 175 * t);
  const ink = Math.round(200 * (1 - t));
  return {
    background: `rgb(${bgR}, ${bgG}, ${bgB})`,
    text: `rgb(${ink}, ${ink}, ${ink})`,
  };
}

const TONE_VOWELS = {
  a: ["ā", "á", "ǎ", "à"],
  e: ["ē", "é", "ě", "è"],
  i: ["ī", "í", "ǐ", "ì"],
  o: ["ō", "ó", "ǒ", "ò"],
  u: ["ū", "ú", "ǔ", "ù"],
  ü: ["ǖ", "ǘ", "ǚ", "ǜ"],
  v: ["ǖ", "ǘ", "ǚ", "ǜ"],
};

const accentedPinyinCache = new Map();

function toAccentedPinyin(numbered) {
  const key = String(numbered);
  const cached = accentedPinyinCache.get(key);
  if (cached !== undefined) return cached;

  const m = key.toLowerCase().match(/^([a-züv:]+)([1-5])$/i);
  if (!m) {
    accentedPinyinCache.set(key, numbered);
    return numbered;
  }

  let base = m[1].replace(/u:/g, "ü").replace(/v/g, "ü");
  const tone = Number(m[2]);
  if (tone < 1 || tone > 4) {
    accentedPinyinCache.set(key, base);
    return base;
  }

  const vowels = [...base]
    .map((ch, i) => ({ ch, i }))
    .filter(({ ch }) => "aeiouü".includes(ch));
  if (!vowels.length) {
    accentedPinyinCache.set(key, base);
    return base;
  }

  let target = vowels[0].i;
  const letters = vowels.map((v) => v.ch);
  if (letters.includes("a")) target = base.indexOf("a");
  else if (letters.includes("e")) target = base.indexOf("e");
  else if (base.includes("ou")) target = base.indexOf("o");
  else target = vowels[vowels.length - 1].i;

  const marked = TONE_VOWELS[base[target]][tone - 1];
  const accented = base.slice(0, target) + marked + base.slice(target + 1);
  accentedPinyinCache.set(key, accented);
  return accented;
}

function fitPinyinEl(el) {
  el.style.fontSize = "";
  const base = parseFloat(getComputedStyle(el).fontSize);
  if (!Number.isFinite(base) || base <= 0) return;

  let lo = 4;
  let hi = base;
  el.style.fontSize = `${hi}px`;
  if (el.scrollWidth <= el.clientWidth) {
    el.style.fontSize = "";
    return;
  }

  for (let i = 0; i < 12; i++) {
    const mid = (lo + hi) / 2;
    el.style.fontSize = `${mid}px`;
    if (el.scrollWidth <= el.clientWidth) lo = mid;
    else hi = mid;
  }
  el.style.fontSize = `${lo}px`;
}

async function fitAllPinyin(root = document) {
  const elements = [...root.querySelectorAll(".cell-pinyin")];
  const total = elements.length;
  if (!total) return;

  setLoadProgress(0, total, "Sizing pinyin");
  await yieldToBrowser();

  for (let i = 0; i < elements.length; i++) {
    fitPinyinEl(elements[i]);
    const done = i + 1;
    if (done === total || done % 40 === 0) {
      setLoadProgress(done, total, "Sizing pinyin");
      await yieldToBrowser();
    }
  }
}

let currentGlossSource = "custom";
let currentHskFilter = "all";
let hideLowestFreq = true;
let hideEmptyAxes = true;
let loadedData = null;
let freqBounds = null;

function ensureFreqBounds(data) {
  if (freqBounds) return freqBounds;
  const counts = collectCounts(data);
  freqBounds = {
    logMin: Math.log(Math.min(...counts)),
    logMax: Math.log(Math.max(...counts)),
  };
  return freqBounds;
}

function currentTones(data) {
  return currentHskFilter === "all"
    ? data.tones
    : data.hsk_tones?.[currentHskFilter] || data.tones;
}

function applyGlossToEl(el, source) {
  const topWordShare = Number(el.dataset.topWordShare);
  const simpleGloss = el.dataset.custom || "";
  const topWordGloss = el.dataset.topWordGloss || "";
  const useTopWord =
    source === "custom" &&
    el.dataset.topWord &&
    topWordGloss &&
    Number.isFinite(topWordShare) &&
    topWordShare >= DOMINANT_WORD_MIN_SHARE;
  const showSimpleWithWord =
    simpleGloss && simpleGloss.toLowerCase() !== topWordGloss.toLowerCase();

  if (useTopWord) {
    const word = el.dataset.topWord;
    const text = `${showSimpleWithWord ? `${simpleGloss}, ` : ""}in ${word}, ${topWordGloss}`;
    el.replaceChildren();
    if (showSimpleWithWord) el.append(`${simpleGloss}, `);
    el.append("in ");
    const zh = document.createElement("span");
    zh.className = "gloss-zh";
    zh.textContent = word;
    el.append(zh, `, ${topWordGloss}`);
    el.title = `${text} · ${Math.round(topWordShare * 100)}% of character uses`;
    return;
  }

  const text = el.dataset[source] || "";
  el.textContent = text;
  el.title = text;
}

function applyGloss(source) {
  currentGlossSource = source;
  document.querySelectorAll(".cell-gloss").forEach((el) => applyGlossToEl(el, source));
}

function fillCellContent(td, cell, logMin, logMax) {
  const colors = frequencyColors(cell.count, logMin, logMax);
  const accented = toAccentedPinyin(cell.pinyin);
  const step = frequencyStep(cell.count, logMin, logMax);

  td.className = "filled";
  td.dataset.freqStep = String(step);
  td.style.backgroundColor = colors.background;
  td.style.color = colors.text;
  td.title = `${accented} · frequency ${cell.count.toLocaleString()}`;

  let wrap = td.querySelector(".cell");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.className = "cell";
    wrap.innerHTML =
      '<div class="cell-top"><div class="cell-char"><span class="cell-char-text"></span></div><div class="cell-pinyin"></div></div><div class="cell-gloss"></div>';
    td.replaceChildren(wrap);
  }

  wrap.querySelector(".cell-char-text").textContent = cell.char;
  wrap.querySelector(".cell-pinyin").textContent = accented;

  const bottom = wrap.querySelector(".cell-gloss");
  const gloss = cell.gloss || {};
  bottom.dataset.custom = gloss.custom || "";
  bottom.dataset.unihan = gloss.unihan || "";
  bottom.dataset.cedict = gloss.cedict || "";
  bottom.dataset.topWord = cell.top_word?.word || "";
  bottom.dataset.topWordGloss = cell.top_word?.gloss || "";
  bottom.dataset.topWordShare = cell.top_word?.share ?? "";
  applyGlossToEl(bottom, currentGlossSource);
}

function clearCellContent(td) {
  td.className = "empty";
  delete td.dataset.freqStep;
  td.removeAttribute("style");
  td.removeAttribute("title");
  td.replaceChildren();
}

function createCell(onset, final, cell, logMin, logMax) {
  const td = document.createElement("td");
  td.dataset.onset = onset;
  td.dataset.final = final;
  if (cell) fillCellContent(td, cell, logMin, logMax);
  else clearCellContent(td);
  return td;
}

function countFilledCharacters(tones, onsets, finals) {
  let total = 0;
  for (const tone of ["1", "2", "3", "4"]) {
    for (const onset of onsets) {
      for (const final of finals) {
        if (tones[tone]?.[onset]?.[final]) total += 1;
      }
    }
  }
  return total;
}

function setLoadProgress(done, total, label = "Loading frequency tables") {
  const status = document.getElementById("status");
  if (!status) return;
  status.hidden = false;
  status.textContent =
    `${label}… [${done.toLocaleString()} / ${total.toLocaleString()} characters]`;
}

function clearLoadStatus() {
  const status = document.getElementById("status");
  if (!status) return;
  status.textContent = "";
  status.hidden = true;
}

async function yieldToBrowser() {
  await new Promise((resolve) => requestAnimationFrame(resolve));
}

async function createToneTable(tone, data, tones, logMin, logMax, progress) {
  const block = document.createElement("details");
  block.className = "tone-block";
  block.dataset.tone = tone;
  block.open = true;

  const heading = document.createElement("summary");
  heading.textContent = TONE_NAMES[tone];
  block.appendChild(heading);

  const scroll = document.createElement("div");
  scroll.className = "table-scroll";

  const table = document.createElement("table");
  table.className = "pinyin-table";
  table.setAttribute("aria-label", TONE_NAMES[tone]);

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  const corner = document.createElement("th");
  corner.className = "corner";
  headRow.appendChild(corner);

  for (const onset of data.onsets) {
    const th = document.createElement("th");
    th.dataset.onset = onset;
    th.textContent = onsetLabel(onset);
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const final of data.finals) {
    const tr = document.createElement("tr");
    tr.dataset.final = final;

    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = finalLabel(final);
    tr.appendChild(th);

    for (const onset of data.onsets) {
      const cell = tones[tone]?.[onset]?.[final];
      tr.appendChild(createCell(onset, final, cell, logMin, logMax));
      if (cell && progress) {
        progress.done += 1;
        if (progress.done === progress.total || progress.done % 40 === 0) {
          setLoadProgress(progress.done, progress.total);
          await yieldToBrowser();
        }
      }
    }
    tbody.appendChild(tr);
  }

  table.appendChild(tbody);
  scroll.appendChild(table);
  block.appendChild(scroll);
  return block;
}

function cellIsPresent(td) {
  if (!td.classList.contains("filled")) return false;
  if (hideLowestFreq && td.dataset.freqStep === "0") return false;
  return true;
}

/** Toggle row/column visibility without rebuilding the tables. */
function applyVisibilityFilters() {
  document.documentElement.classList.toggle("hide-lowest-freq", hideLowestFreq);

  document.querySelectorAll(".tone-block").forEach((block) => {
    const table = block.querySelector(".pinyin-table");
    if (!table) return;

    const onsetHas = new Map();
    const finalHas = new Map();
    for (const onset of loadedData.onsets) onsetHas.set(onset, false);
    for (const final of loadedData.finals) finalHas.set(final, false);

    table.querySelectorAll("td[data-onset]").forEach((td) => {
      if (!cellIsPresent(td)) return;
      onsetHas.set(td.dataset.onset, true);
      finalHas.set(td.dataset.final, true);
    });

    table.querySelectorAll("thead th[data-onset]").forEach((th) => {
      th.classList.toggle(
        "axis-hidden",
        hideEmptyAxes && !onsetHas.get(th.dataset.onset)
      );
    });

    table.querySelectorAll("tbody tr[data-final]").forEach((tr) => {
      tr.classList.toggle(
        "axis-hidden",
        hideEmptyAxes && !finalHas.get(tr.dataset.final)
      );
    });

    table.querySelectorAll("td[data-onset]").forEach((td) => {
      td.classList.toggle(
        "axis-hidden",
        hideEmptyAxes && !onsetHas.get(td.dataset.onset)
      );
    });
  });
}

/** Update cell contents in place when the HSK corpus subset changes. */
function updateCellsForCurrentFilter() {
  const { logMin, logMax } = ensureFreqBounds(loadedData);
  const tones = currentTones(loadedData);

  document.querySelectorAll(".tone-block").forEach((block) => {
    const tone = block.dataset.tone;
    block.querySelectorAll("td[data-onset]").forEach((td) => {
      const cell = tones[tone]?.[td.dataset.onset]?.[td.dataset.final];
      if (cell) fillCellContent(td, cell, logMin, logMax);
      else clearCellContent(td);
    });
  });
}

async function buildTables(data) {
  const { logMin, logMax } = ensureFreqBounds(data);
  const tones = currentTones(data);
  const total = countFilledCharacters(tones, data.onsets, data.finals);
  const progress = { done: 0, total };
  setLoadProgress(0, total);

  const root = document.getElementById("tables");
  const fragment = document.createDocumentFragment();
  for (const tone of ["1", "2", "3", "4"]) {
    fragment.appendChild(
      await createToneTable(tone, data, tones, logMin, logMax, progress)
    );
  }
  root.replaceChildren(fragment);
  await yieldToBrowser();
  await fitAllPinyin(root);
  applyVisibilityFilters();
  clearLoadStatus();
}

function initGlossToggle() {
  const inputs = document.querySelectorAll('input[name="gloss"]');
  const checked = document.querySelector('input[name="gloss"]:checked');
  if (checked) currentGlossSource = checked.value;
  inputs.forEach((input) => {
    input.addEventListener("change", (e) => {
      if (e.target.checked) applyGloss(e.target.value);
    });
  });
}

function initHskToggle() {
  const inputs = document.querySelectorAll('input[name="hsk"]');
  const checked = document.querySelector('input[name="hsk"]:checked');
  if (checked) currentHskFilter = checked.value;
  inputs.forEach((input) => {
    input.addEventListener("change", (event) => {
      if (!event.target.checked || !loadedData) return;
      currentHskFilter = event.target.value;
      updateCellsForCurrentFilter();
      applyVisibilityFilters();
    });
  });
}

function initDisplayToggles() {
  const lowest = document.getElementById("hide-lowest-freq");
  const emptyAxes = document.getElementById("hide-empty-axes");
  if (lowest) {
    hideLowestFreq = lowest.checked;
    lowest.addEventListener("change", () => {
      hideLowestFreq = lowest.checked;
      applyVisibilityFilters();
    });
  }
  if (emptyAxes) {
    hideEmptyAxes = emptyAxes.checked;
    emptyAxes.addEventListener("change", () => {
      hideEmptyAxes = emptyAxes.checked;
      applyVisibilityFilters();
    });
  }
}

function setPanelHidden(hidden) {
  const app = document.querySelector(".app");
  const hideButton = document.getElementById("hide-panel-button");
  const showButton = document.getElementById("show-panel-button");
  if (!app || !hideButton || !showButton) return;

  app.classList.toggle("panel-hidden", hidden);
  hideButton.setAttribute("aria-expanded", String(!hidden));
  showButton.setAttribute("aria-expanded", String(!hidden));
  showButton.hidden = !hidden;
}

function initPanelToggle() {
  const hideButton = document.getElementById("hide-panel-button");
  const showButton = document.getElementById("show-panel-button");
  if (!hideButton || !showButton) return;

  setPanelHidden(true);
  hideButton.addEventListener("click", () => setPanelHidden(true));
  showButton.addEventListener("click", () => setPanelHidden(false));
}

async function main() {
  const status = document.getElementById("status");
  initGlossToggle();
  initHskToggle();
  initDisplayToggles();
  initPanelToggle();
  try {
    const res = await fetch("./data/tables.json");
    if (!res.ok) throw new Error(`Failed to load tables.json (${res.status})`);
    loadedData = await res.json();
    await buildTables(loadedData);
  } catch (err) {
    console.error(err);
    status.hidden = false;
    status.textContent =
      "Could not load data/tables.json. Serve the project over HTTP (GitHub Pages or a local static server).";
  }
}

main();
