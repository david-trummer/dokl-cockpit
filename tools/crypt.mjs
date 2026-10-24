// Dokl Cockpit · Verschlüsselung der Gesellschafter-Daten (Node >= 18, keine Abhängigkeiten)
//
//   node crypt.mjs init <secrets.json>                    neuen Datenschlüssel anlegen
//   node crypt.mjs add-user <secrets.json> <name>         Benutzer anlegen, Passwort wird erzeugt und ausgegeben
//   node crypt.mjs remove-user <secrets.json> <name>      Benutzer entfernen UND Datenschlüssel erneuern
//   node crypt.mjs rotate <secrets.json>                  Datenschlüssel erneuern (alle Passwörter bleiben)
//   node crypt.mjs encrypt <secrets.json> <export-dir> <out/data.enc.json>
//        export-dir = ArtifactData-Export mit tage/, wochen/, config/, plan/ (je ein JSON pro Dokument)
//
// secrets.json gehört NIE ins Repository. Aufbau: {kv, k (base64, 32 Byte), users:{name:passwort}}
// Format data.enc.json: {v:1, kv, stand, kdf:{name,hash,iter}, keys:{uid:{salt,iv,wk}}, iv, ct}
//   uid = erste 32 Hex-Zeichen von SHA-256("dokl-cockpit:" + name klein) – verrät den Namen nicht direkt
//   wk  = Datenschlüssel, AES-256-GCM-verschlüsselt mit PBKDF2(passwort, salt, iter)
//   ct  = gzip(JSON) AES-256-GCM-verschlüsselt mit dem Datenschlüssel
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
const { subtle } = globalThis.crypto;
const getRandomValues = (a) => globalThis.crypto.getRandomValues(a);
const ITER = 600000;
const b64 = (u) => Buffer.from(u).toString('base64');
const unb64 = (s) => new Uint8Array(Buffer.from(s, 'base64'));
const rnd = (n) => getRandomValues(new Uint8Array(n));
const te = new TextEncoder();

const readJ = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));
const writeJ = (p, o) => fs.writeFileSync(p, JSON.stringify(o, null, 1), { mode: 0o600 });

function newPassword() {
  const A = 'abcdefghjkmnpqrstuvwxyz23456789'; // ohne 0/o/1/l/i
  const r = rnd(20);
  let s = '';
  for (let i = 0; i < 20; i++) { s += A[r[i] % A.length]; if (i % 5 === 4 && i < 19) s += '-'; }
  return s; // 20 Zeichen aus 31 → ~99 Bit
}
async function uidOf(name) {
  const d = await subtle.digest('SHA-256', te.encode('dokl-cockpit:' + name.trim().toLowerCase()));
  return Buffer.from(d).toString('hex').slice(0, 32);
}
async function wrap(raw, pw) {
  const salt = rnd(16), iv = rnd(12);
  const base = await subtle.importKey('raw', te.encode(pw), 'PBKDF2', false, ['deriveKey']);
  const kek = await subtle.deriveKey({ name: 'PBKDF2', salt, iterations: ITER, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
  const wk = await subtle.encrypt({ name: 'AES-GCM', iv }, kek, raw);
  return { salt: b64(salt), iv: b64(iv), wk: b64(wk) };
}
function loadExport(dir) {
  const col = (c) => {
    const d = path.join(dir, c);
    if (!fs.existsSync(d)) return [];
    return fs.readdirSync(d).filter((f) => f.endsWith('.json')).map((f) => {
      const o = readJ(path.join(d, f));
      return { id: f.slice(0, -5), data: o.data && typeof o.data === 'object' && !Array.isArray(o.data) && ('datum' in o.data || 'jahr' in o.data || 'gastro' in o.data) ? o.data : o };
    });
  };
  const tage = col('tage').map((x) => x.data).filter((t) => t && t.datum);
  // Personaldetails entfernen – diese Felder verlassen Claude nie
  for (const t of tage) {
    if (t.gastro) { for (const f of ['staff', 'trinkgeld', 'intern', 'intern_netto']) delete t.gastro[f]; }
    delete t.quelle;
  }
  const cfg = Object.fromEntries(col('config').map((x) => [x.id, x.data]));
  return {
    tage,
    wochen: col('wochen').map((x) => x.data),
    plan: col('plan').map((x) => x.data),
    ziele: cfg.ziele || null,
    betrieb: cfg.betrieb ? { zimmer: cfg.betrieb.zimmer } : null,
  };
}

const [cmd, sp, ...rest] = process.argv.slice(2);
if (!cmd || !sp) { console.error('Aufruf siehe Kopf der Datei'); process.exit(2); }

if (cmd === 'init') {
  if (fs.existsSync(sp)) { console.error('existiert schon: ' + sp); process.exit(1); }
  writeJ(sp, { kv: 1, k: b64(rnd(32)), users: {} });
  console.log('Datenschlüssel angelegt.');
} else {
  const S = readJ(sp);
  if (cmd === 'add-user') {
    const name = rest[0];
    if (!name || !/^[a-z0-9._-]{2,40}$/i.test(name)) { console.error('Benutzername: 2–40 Zeichen a–z, 0–9, . _ -'); process.exit(1); }
    if (Object.keys(S.users).some((u) => u.toLowerCase() === name.toLowerCase())) { console.error('gibt es schon'); process.exit(1); }
    S.users[name] = newPassword();
    writeJ(sp, S);
    console.log(`${name}\t${S.users[name]}`);
  } else if (cmd === 'remove-user' || cmd === 'rotate') {
    if (cmd === 'remove-user') {
      const k = Object.keys(S.users).find((u) => u.toLowerCase() === (rest[0] || '').toLowerCase());
      if (!k) { console.error('unbekannt'); process.exit(1); }
      delete S.users[k];
    }
    S.k = b64(rnd(32)); S.kv = (S.kv || 1) + 1;
    writeJ(sp, S);
    console.log('Datenschlüssel erneuert (Version ' + S.kv + '). Gespeicherte Anmeldungen auf Geräten werden ungültig.');
  } else if (cmd === 'encrypt') {
    const [dir, out] = rest;
    const D = loadExport(dir);
    if (!D.tage.length) { console.error('keine Tagesdaten im Export'); process.exit(1); }
    const raw = unb64(S.k);
    const key = await subtle.importKey('raw', raw, 'AES-GCM', false, ['encrypt']);
    const iv = rnd(12);
    const ct = await subtle.encrypt({ name: 'AES-GCM', iv }, key, zlib.gzipSync(Buffer.from(JSON.stringify(D))));
    const keys = {};
    for (const [name, pw] of Object.entries(S.users)) keys[await uidOf(name)] = await wrap(raw, pw);
    const stand = D.tage.map((t) => t.datum).sort().pop();
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, JSON.stringify({ v: 1, kv: S.kv, stand, kdf: { name: 'PBKDF2', hash: 'SHA-256', iter: ITER }, keys, iv: b64(iv), ct: b64(ct) }));
    console.log(`verschlüsselt: ${D.tage.length} Tage bis ${stand}, ${D.wochen.length} Wochen, ${D.plan.length} Pläne, ${Object.keys(keys).length} Benutzer → ${out}`);
  } else { console.error('unbekannter Befehl'); process.exit(2); }
}
