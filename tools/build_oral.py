"""Insère le mode « anglais à l'oral » (moteur d'Aleph) directement dans index.html.
Usage, depuis la racine du dépôt : python3 tools/build_oral.py"""
import re
css = open('tools/oral.css', encoding='utf-8').read()
tpl = open('tools/oral-template.html', encoding='utf-8').read()
# --- CSS : seulement l'écran de séance, limité à #oralDrive pour ne rien casser dans la Ruche
root = re.search(r':root\{(.*?)\}', css, re.S).group(1).replace('color-scheme:dark;', '')
drive = css[css.index('/* Écran de conduite */'):]
drive += '\n.stop{position:absolute;bottom:calc(20px + env(safe-area-inset-bottom,0px));left:50%;transform:translateX(-50%);font:inherit;font-weight:700;color:var(--ink);background:transparent;border:2px solid var(--line);border-radius:99px;padding:12px 28px;cursor:pointer}\n'
def scope_sel(sel):
    sel = sel.strip()
    if sel.startswith('.drive') or re.match(r'\.(listening|ok|bad|classic)\b', sel): return '#oralDrive' + sel
    return '#oralDrive ' + sel
def scope(block):
    block = re.sub(r'/\*.*?\*/', '', block, flags=re.S)
    out = []
    for m in re.finditer(r'(@media[^{]*)\{((?:[^{}]*\{[^{}]*\})*)\s*\}|(@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\})*\s*\})|([^{}@]+)\{([^{}]*)\}', block):
        if m.group(1): out.append(m.group(1) + '{' + scope(m.group(2)) + '}')
        elif m.group(3): out.append(m.group(3))
        else:
            sels = [s for s in m.group(4).split(',') if s.strip() and not s.strip().startswith('/*')]
            sels = [re.sub(r'/\*.*?\*/', '', s, flags=re.S) for s in sels]
            out.append(','.join(scope_sel(s) for s in sels if s.strip()) + '{' + m.group(5) + '}')
    return '\n'.join(out)
scoped = '#oralDrive{' + root + 'font-family:var(--f-body);color:var(--ink);font-size:17px;line-height:1.45}\n' + scope(drive)
# --- HTML de l'écran de séance (repris du modèle)
html = tpl[tpl.index('<section class="drive" id="drive"'):tpl.index('</section>', tpl.index('<section class="drive" id="drive"')) + 10]
html = html.replace('id="drive"', 'id="oralDrive"')
# --- JS : le moteur d'Aleph (boîtes, comparaison, voix, écoute, séance), sans l'écran d'accueil
js = tpl[tpl.index('<script>') + 8:tpl.index('</script>')]
eng = js[js.index('/* ---------- Boîtes de Leitner'):js.index('/* ---------- Accueil')] + js[js.index('/* ---------- Séance'):js.index("$('start').onclick")]
eng = eng.replace('function record(', 'function recordO(').replace("record(c.id, true); ruchePoint(c.id);", "recordO(c.id, true); if (!S.first[c.id]) { S.first[c.id] = 1; record(c.id, true); }")
eng = eng.replace("record(c.id, false);", "recordO(c.id, false); if (!S.first[c.id]) { S.first[c.id] = 1; record(c.id, false); }")
eng = eng.replace("$('drive')", "$('oralDrive')")
# fin de séance : retour à l'accueil de la Ruche
eng = eng.replace("S = null; $('oralDrive').hidden = true; $('home').hidden = false; refreshHome();", "S = null; $('oralDrive').hidden = true; document.body.style.overflow = ''; save(); home();")
eng = eng.replace("if (msg) { $('warn').innerHTML = msg; $('warn').hidden = false; }", "if (msg) setTimeout(() => alert(msg), 50);")
start = tpl[tpl.index("$('start').onclick = async () => {"):tpl.index("document.addEventListener('visibilitychange'")]
start = start.replace("$('start').onclick = async () => {\n  if (!active().length) return;", "window.startOral = async function (themes, dir, len) {\n  st.prefs.themes = themes; st.prefs.dir = dir === 'en-fr' ? 'en-fr' : 'fr-en'; st.prefs.len = len || 0; saveO();\n  if (!SR) { alert(\"La reconnaissance vocale n'est pas disponible sur ce navigateur. Utilise Chrome sur Android, ou Safari sur iPhone.\"); return; }\n  if (IOS && navigator.standalone) { alert(\"Sur iPhone, l'oral ne marche que dans Safari : depuis l'icône de l'écran d'accueil, Apple coupe le micro. Ouvre onizard.github.io/ruche dans Safari.\"); return; }")
start = start.replace("S = { on: true,", "S = { first: {}, on: true,").replace("$('home').hidden = true; $('drive').hidden = false;", "$('oralDrive').hidden = false; document.body.style.overflow = 'hidden';")
start = start.replace("const s = await navigator.mediaDevices", "const s = await navigator.mediaDevices")
head = """
const $ = id => document.getElementById(id);
const OCARDS = CARDS.filter(c => c.subject === 'anglais');
const KEY = 'ruche-oral-v1';
let st = { boxes: {}, n: 0, prefs: { dir: 'fr-en', len: 20, themes: [] } };
try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.boxes) st = { ...st, ...s, prefs: { ...st.prefs, ...s.prefs } }; } catch (e) {}
const saveO = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
const active = () => OCARDS.filter(c => st.prefs.themes.includes(c.theme));
"""
eng = eng.replace('save();', 'saveO();').replace("st.boxes[id] = b; saveO();", "st.boxes[id] = b; saveO();")
# ruchePoint n'est plus utile : record() de la Ruche compte déjà les points du bonus
eng = re.sub(r"// une bonne réponse du premier coup rapporte.*?\n\}\n", "", eng, flags=re.S)
eng = eng.replace("stopSession(); }\n}", "stopSession(); }\n}", 1)
engine = '(() => {' + head + eng + start + '})();'
engine = engine.replace("S = null; $('oralDrive').hidden = true; document.body.style.overflow = ''; saveO(); home();", "S = null; $('oralDrive').hidden = true; document.body.style.overflow = ''; save(); home();")
# préfixe « o- » sur toutes les classes de l'écran de séance : la Ruche a déjà des classes .bar, .prompt, .ok, .bad…
names = sorted(set(re.findall(r'\.([a-zA-Z][\w-]*)', re.sub(r'\{[^{}]*\}', '{}', scoped))), key=len, reverse=True)
names = [n for n in names if not n[0].isdigit()]
for n in names: scoped = re.sub(r'\.' + re.escape(n) + r'(?![\w-])', '.o-' + n, scoped)
html = re.sub(r'class="([^"]*)"', lambda m: 'class="' + ' '.join('o-' + c if c in names else c for c in m.group(1).split()) + '"', html)
engine = engine.replace("closest('.cface')", "closest('.o-cface')").replace("contains('ctag')", "contains('o-ctag')")
for n in ['flipped', 'deal', 'revealed', 'instant']: engine = engine.replace("'" + n + "'", "'o-" + n + "'")
engine = engine.replace("$('oralDrive').className = 'drive ' + (cls || '');", "$('oralDrive').className = 'o-drive ' + (cls || '').split(' ').filter(Boolean).map(x => 'o-' + x).join(' ');")
block = '<!--ORAL-START-->\n<style>\n' + scoped + '\n</style>\n' + html + '\n<script>\n' + engine + '\n</script>\n<!--ORAL-END-->\n'
idx = open('index.html', encoding='utf-8').read()
idx = re.sub(r'<!--ORAL-START-->.*?<!--ORAL-END-->\n', '', idx, flags=re.S)
mark = '<script>if ("serviceWorker" in navigator)'
idx = idx.replace(mark, block + mark, 1)
open('index.html', 'w', encoding='utf-8').write(idx)
print('ok', len(block))
