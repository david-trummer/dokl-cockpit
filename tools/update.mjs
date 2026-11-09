// Dokl Cockpit · inkrementelles Daten-Update (Node >= 18, keine Abhängigkeiten)
//
//   node update.mjs show  <schluessel.json> <data.enc.json>
//        gibt {stand, versionen:{datum:version}} aus (Klartext-Zahlen werden NICHT ausgegeben)
//   node update.mjs merge <schluessel.json> <data.enc.json> <neu-dir> <out/data.enc.json>
//        neu-dir/tage/<datum>.json   = {"version":n,"data":{...}}   (Tag ersetzen/ergänzen)
//        neu-dir/wochen/<id>.json    = {"version":n,"data":{...}}   (Woche ersetzen/ergänzen, Schlüssel: jahr+kw bzw. id)
//        Benutzerschlüssel (keys) bleiben unverändert; nur Nutzdaten + iv + stand werden neu geschrieben.
// Personaldetails werden auch hier gefiltert (staff, trinkgeld, intern, intern_netto, quelle).
// Die Schlüsseldatei gehört NIE ins Repository.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
const { subtle } = globalThis.crypto;
const b64 = (u) => Buffer.from(u).toString('base64');
const unb64 = (s) => new Uint8Array(Buffer.from(s, 'base64'));
const readJ = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));

async function decrypt(S, E) {
  if (E.kv !== S.kv) throw new Error(`Schlüsselversion passt nicht (Datei ${E.kv}, Schlüssel ${S.kv})`);
  const key = await subtle.importKey('raw', unb64(S.k), 'AES-GCM', false, ['decrypt']);
  const pt = await subtle.decrypt({ name: 'AES-GCM', iv: unb64(E.iv) }, key, unb64(E.ct));
  return JSON.parse(zlib.gunzipSync(Buffer.from(pt)).toString('utf8'));
}
function clean(t) {
  if (t.gastro) for (const f of ['staff', 'trinkgeld', 'intern', 'intern_netto']) delete t.gastro[f];
  delete t.quelle;
  return t;
}
const wkey = (w) => w.id ?? (w.jahr != null && w.kw != null ? `${w.jahr}-${w.kw}` : w.von ?? JSON.stringify(w).slice(0, 80));
function readNeu(dir, col) {
  const d = path.join(dir, col);
  if (!fs.existsSync(d)) return [];
  return fs.readdirSync(d).filter((f) => f.endsWith('.json')).map((f) => {
    const o = readJ(path.join(d, f));
    const hasWrap = o && typeof o === 'object' && 'data' in o && 'version' in o;
    return { id: f.slice(0, -5), version: hasWrap ? o.version : 1, data: hasWrap ? o.data : o };
  });
}

const [cmd, sp, ep, ...rest] = process.argv.slice(2);
if (!cmd || !sp || !ep) { console.error('Aufruf siehe Kopf der Datei'); process.exit(2); }
const S = readJ(sp), E = readJ(ep);
const D = await decrypt(S, E);
D.versionen ??= {};
if (cmd === 'show') {
  const stand = D.tage.map((t) => t.datum).sort().pop();
  console.log(JSON.stringify({ stand, versionen: Object.fromEntries(D.tage.map((t) => [t.datum, D.versionen[t.datum] ?? 1])) }));
} else if (cmd === 'merge') {
  const [neu, out] = rest;
  const tage = new Map(D.tage.map((t) => [t.datum, t]));
  let n = 0;
  for (const x of readNeu(neu, 'tage')) {
    const t = clean(x.data);
    if (!t.datum) throw new Error('Tag ohne datum: ' + x.id);
    tage.set(t.datum, t); D.versionen[t.datum] = x.version; n++;
  }
  D.tage = [...tage.values()].sort((a, b) => a.datum.localeCompare(b.datum));
  const wochen = new Map(D.wochen.map((w) => [wkey(w), w]));
  let nw = 0;
  for (const x of readNeu(neu, 'wochen')) { wochen.set(wkey(x.data), x.data); nw++; }
  D.wochen = [...wochen.values()];
  const key = await subtle.importKey('raw', unb64(S.k), 'AES-GCM', false, ['encrypt']);
  const iv = globalThis.crypto.getRandomValues(new Uint8Array(12));
  const ct = await subtle.encrypt({ name: 'AES-GCM', iv }, key, zlib.gzipSync(Buffer.from(JSON.stringify(D))));
  const stand = D.tage.map((t) => t.datum).sort().pop();
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify({ ...E, stand, iv: b64(iv), ct: b64(ct) }));
  console.log(`zusammengeführt: ${n} Tage, ${nw} Wochen neu/aktualisiert, Stand ${stand}`);
} else { console.error('unbekannter Befehl'); process.exit(2); }
