"""Construit oral.html (anglais à l'oral) à partir des leçons d'anglais de index.html.
Usage : python3 tools/build_oral.py   (depuis la racine du dépôt)"""
import re, json
src = open('index.html', encoding='utf-8').read()
block = src[src.index('const THEMES = ['):src.index('THEMES.forEach(t => t.subject')]
themes = []
for m in re.finditer(r"\{id:'([^']+)',\s*nom:(['\"])(.*?)\2,\s*sous:(['\"])(.*?)\4,\s*data:`(.*?)`\}", block, re.S):
    tid, nom, data = m.group(1), m.group(3), m.group(6)
    cards = []
    for raw in data.split('\n'):
        if not raw.strip(): continue
        p = [x.strip() for x in raw.split('|')] + ['', '', '']
        fr, en, alt, note = p[0], p[1], p[2], p[3]
        cards.append([fr, en, [a.strip() for a in alt.split(';') if a.strip()], note])
    themes.append({'id': tid, 'nom': nom, 'cards': cards})
tpl = open('tools/oral-template.html', encoding='utf-8').read()
out = tpl.replace('/*__CSS__*/', open('tools/oral.css', encoding='utf-8').read()).replace('__DATA__', json.dumps(themes, ensure_ascii=False))
open('oral.html', 'w', encoding='utf-8').write(out)
print(len(themes), 'leçons,', sum(len(t['cards']) for t in themes), 'mots')
