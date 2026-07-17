const TONE_NAMES = {
  1: "Tone 1 (high level)",
  2: "Tone 2 (rising)",
  3: "Tone 3 (dipping)",
  4: "Tone 4 (falling)",
};

// When Simple gloss is selected, show a dominant multi-character word instead.
const DOMINANT_WORD_MIN_SHARE = 0.6;

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

const FREQ_STEPS = 4;

/** Continuous log position in [0, 1], then snapped to 0 .. FREQ_STEPS-1. */
function frequencyStep(count, logMin, logMax) {
  const log = Math.log(Math.max(count, 1));
  const t =
    logMax === logMin ? 1 : Math.min(1, Math.max(0, (log - logMin) / (logMax - logMin)));
  return Math.min(FREQ_STEPS - 1, Math.floor(t * FREQ_STEPS));
}

/** Stepped white→green background and grey→black text (log space, 10 steps). */
function frequencyColors(count, logMin, logMax) {
  const step = frequencyStep(count, logMin, logMax);
  const t = step / (FREQ_STEPS - 1);

  // white → green
  const bgR = Math.round(255 - 210 * t);
  const bgG = Math.round(255 - 55 * t);
  const bgB = Math.round(255 - 175 * t);

  // light grey → black
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

/** Convert numbered pinyin (e.g. wo3) to accented form (wǒ). */
function toAccentedPinyin(numbered) {
  const m = String(numbered).toLowerCase().match(/^([a-züv:]+)([1-5])$/i);
  if (!m) return numbered;

  let base = m[1].replace(/u:/g, "ü").replace(/v/g, "ü");
  const tone = Number(m[2]);
  if (tone < 1 || tone > 4) return base;

  const vowels = [...base].map((ch, i) => ({ ch, i })).filter(({ ch }) => "aeiouü".includes(ch));
  if (!vowels.length) return base;

  let target = vowels[0].i;
  const letters = vowels.map((v) => v.ch);
  if (letters.includes("a")) {
    target = base.indexOf("a");
  } else if (letters.includes("e")) {
    target = base.indexOf("e");
  } else if (base.includes("ou")) {
    target = base.indexOf("o");
  } else {
    target = vowels[vowels.length - 1].i;
  }

  const vowel = base[target];
  const marked = TONE_VOWELS[vowel][tone - 1];
  return base.slice(0, target) + marked + base.slice(target + 1);
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

  // Binary search the largest size that fits on one line
  for (let i = 0; i < 12; i++) {
    const mid = (lo + hi) / 2;
    el.style.fontSize = `${mid}px`;
    if (el.scrollWidth <= el.clientWidth) lo = mid;
    else hi = mid;
  }
  el.style.fontSize = `${lo}px`;
}

function fitAllPinyin(root = document) {
  root.querySelectorAll(".cell-pinyin").forEach(fitPinyinEl);
}

function createCell(cell, logMin, logMax) {
  const td = document.createElement("td");
  if (!cell) {
    td.className = "empty";
    return td;
  }

  td.className = "filled";
  const colors = frequencyColors(cell.count, logMin, logMax);
  td.style.backgroundColor = colors.background;
  td.style.color = colors.text;
  const accented = toAccentedPinyin(cell.pinyin);
  td.title = `${accented} · frequency ${cell.count.toLocaleString()}`;

  const wrap = document.createElement("div");
  wrap.className = "cell";

  const top = document.createElement("div");
  top.className = "cell-top";

  const char = document.createElement("div");
  char.className = "cell-char";
  const charText = document.createElement("span");
  charText.className = "cell-char-text";
  charText.textContent = cell.char;
  char.appendChild(charText);

  const pinyin = document.createElement("div");
  pinyin.className = "cell-pinyin";
  pinyin.textContent = accented;

  top.append(char, pinyin);

  const bottom = document.createElement("div");
  bottom.className = "cell-gloss";
  const gloss = cell.gloss || {};
  bottom.dataset.custom = gloss.custom || "";
  bottom.dataset.unihan = gloss.unihan || "";
  bottom.dataset.cedict = gloss.cedict || "";
  bottom.dataset.topWord = cell.top_word?.word || "";
  bottom.dataset.topWordGloss = cell.top_word?.gloss || "";
  bottom.dataset.topWordShare = cell.top_word?.share ?? "";
  applyGlossToEl(bottom, currentGlossSource);

  wrap.append(top, bottom);
  td.appendChild(wrap);
  return td;
}

let currentGlossSource = "custom";

function applyGlossToEl(el, source) {
  const topWordShare = Number(el.dataset.topWordShare);
  const useTopWord =
    source === "custom" &&
    el.dataset.topWord &&
    el.dataset.topWordGloss &&
    Number.isFinite(topWordShare) &&
    topWordShare >= DOMINANT_WORD_MIN_SHARE;
  const text = useTopWord
    ? `in ${el.dataset.topWord}, ${el.dataset.topWordGloss}`
    : el.dataset[source] || "";
  el.textContent = text;
  el.title = useTopWord
    ? `${text} · ${Math.round(topWordShare * 100)}% of character uses`
    : text;
}

function applyGloss(source) {
  currentGlossSource = source;
  document.querySelectorAll(".cell-gloss").forEach((el) => applyGlossToEl(el, source));
}

function createToneTable(tone, data, tones, logMin, logMax) {
  const block = document.createElement("section");
  block.className = "tone-block";
  block.id = `tone-${tone}`;

  const filled = data.onsets.reduce((n, onset) => {
    const row = tones[tone]?.[onset] || {};
    return n + Object.keys(row).length;
  }, 0);

  const heading = document.createElement("h2");
  heading.innerHTML = `${TONE_NAMES[tone]} <span class="tone-meta">${filled} syllables</span>`;
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
  corner.textContent = "coda \\ onset";
  headRow.appendChild(corner);

  for (const onset of data.onsets) {
    const th = document.createElement("th");
    th.textContent = onsetLabel(onset);
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const final of data.finals) {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = finalLabel(final);
    tr.appendChild(th);

    for (const onset of data.onsets) {
      const cell = tones[tone]?.[onset]?.[final];
      tr.appendChild(createCell(cell, logMin, logMax));
    }
    tbody.appendChild(tr);
  }

  table.appendChild(tbody);
  scroll.appendChild(table);
  block.appendChild(scroll);
  return block;
}

let currentHskFilter = "all";
let loadedData = null;

function render(data) {
  const counts = collectCounts(data);
  const logMin = Math.log(Math.min(...counts));
  const logMax = Math.log(Math.max(...counts));
  const tones =
    currentHskFilter === "all"
      ? data.tones
      : data.hsk_tones?.[currentHskFilter] || data.tones;

  const root = document.getElementById("tables");
  root.replaceChildren();
  for (const tone of ["1", "2", "3", "4"]) {
    root.appendChild(createToneTable(tone, data, tones, logMin, logMax));
  }

  document.getElementById("corpus-label").textContent = data.corpus;
  const stats = data.stats;
  const filled =
    currentHskFilter === "all"
      ? stats.filled_cells
      : stats.filled_cells_by_hsk?.[currentHskFilter] || 0;
  const filterLabel =
    currentHskFilter === "all" ? "" : `HSK ${currentHskFilter} and below · `;
  document.getElementById("status").textContent =
    `${filterLabel}${filled} filled cells from ${stats.characters_in_corpus.toLocaleString()} corpus characters.`;

  requestAnimationFrame(() => fitAllPinyin(root));
}

let resizeTimer = 0;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => fitAllPinyin(), 100);
});

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
      if (!event.target.checked) return;
      currentHskFilter = event.target.value;
      if (loadedData) render(loadedData);
    });
  });
}

async function main() {
  const status = document.getElementById("status");
  initGlossToggle();
  initHskToggle();
  try {
    const res = await fetch("./data/tables.json");
    if (!res.ok) throw new Error(`Failed to load tables.json (${res.status})`);
    loadedData = await res.json();
    render(loadedData);
  } catch (err) {
    console.error(err);
    status.textContent =
      "Could not load data/tables.json. Serve the project over HTTP (GitHub Pages or a local static server).";
  }
}

main();
