// Renders privacy.html / imprint.html from window.LEGAL in the language from ?lang= (or the device language)
(function () {
  const page = document.body.dataset.page, other = page === 'privacy' ? 'imprint' : 'privacy';
  const langs = ['de', 'en', 'es', 'pt', 'fr', 'it', 'ru', 'zh', 'ja', 'ar'].filter(l => LEGAL[l]);
  const names = { de: 'Deutsch', en: 'English', es: 'Español', pt: 'Português', fr: 'Français', it: 'Italiano', ru: 'Русский', zh: '中文', ja: '日本語', ar: 'العربية' };
  const q = new URLSearchParams(location.search).get('lang');
  let lang = langs.includes(q) ? q : (navigator.languages || [navigator.language || 'en']).map(l => String(l).slice(0, 2).toLowerCase()).find(l => langs.includes(l)) || 'en';
  const fill = s => s.replace(/\{(name|address|email)\}/g, (m, k) => CONTACT[k]);
  const link = s => {   // text with URLs -> nodes with clickable links
    const frag = document.createDocumentFragment();
    fill(s).split(/(https?:\/\/[^\s)]+)/).forEach((part, i) => {
      if (i % 2) { const a = document.createElement('a'); a.href = part; a.textContent = part; a.rel = 'noopener'; frag.appendChild(a); }
      else frag.appendChild(document.createTextNode(part));
    });
    return frag;
  };
  function render() {
    const L = LEGAL[lang], P = L[page];
    document.documentElement.lang = lang; document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.title = P.title + ' – Mountain Ride';
    const main = document.getElementById('main'); main.replaceChildren();
    const h1 = document.createElement('h1'); h1.textContent = P.title; main.appendChild(h1);
    for (const [head, text] of P.sections) {
      if (head) { const h = document.createElement('h2'); h.textContent = head; main.appendChild(h); }
      for (const para of text.split('\n\n')) { const p = document.createElement('p'); p.appendChild(link(para)); main.appendChild(p); }
    }
    if (P.updated) { const u = document.createElement('p'); u.className = 'updated'; u.textContent = P.updated; main.appendChild(u); }
    document.getElementById('langLabel').textContent = L.lang;
    const o = document.getElementById('other'); o.textContent = L.other[page]; o.href = other + '.html?lang=' + lang;
  }
  const sel = document.getElementById('lang');
  for (const l of langs) { const opt = document.createElement('option'); opt.value = l; opt.textContent = names[l]; sel.appendChild(opt); }
  sel.value = lang;
  sel.addEventListener('change', () => { lang = sel.value; history.replaceState(null, '', '?lang=' + lang); render(); });
  render();
})();
