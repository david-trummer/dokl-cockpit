"""Erzeugt die Gesellschafter-Version (site/index.html) aus dem Claude-Cockpit (Dokl_Tagescockpit.html).

Änderungen gegenüber dem Original:
- keine Claude-Datenbank: Daten kommen verschlüsselt aus data.enc.json und werden im Browser
  mit Benutzername + Passwort entschlüsselt (AES-256-GCM, Schlüssel je Person über PBKDF2)
- ohne Personaldetails: kein Trinkgeld, kein interner Verbrauch, keine Bediener, keine internen Konten
- nur lesen: kein Planungs-Reiter, keine Zimmeranzahl-Eingabe, kein „Planung bearbeiten“

Aufruf: python3 build_site.py <Dokl_Tagescockpit.html> <ausgabe/index.html>
Jede Ersetzung muss genau einmal greifen, sonst bricht das Skript ab (Schutz bei Änderungen am Original).
"""
import sys, pathlib

src, dst = sys.argv[1], sys.argv[2]
h = pathlib.Path(src).read_text(encoding='utf-8')

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit(f'Ersetzung greift {n}x statt {count}x: {old[:80]!r}')
    h = h.replace(old, new)

# ---- Kopf: eigenständiges Dokument mit Titel im <head>, kein Suchmaschinen-Index
rep('<title>Dokl Tagescockpit</title>\n', '')
rep('<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">',
    '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer">'
    '<title>Dokl Cockpit · Gesellschafter</title>')

# ---- Login-Stile
LOGIN_CSS = '''
body.locked .tabs,body.locked .ctrl,body.locked #status{display:none}
.login{max-width:380px;margin:40px auto;display:flex;flex-direction:column;gap:12px}
.login h2{margin:0;font-family:Petrona,Georgia,serif;font-size:22px}
.login label{display:flex;flex-direction:column;gap:4px;font-size:13.5px;color:var(--ink-2)}
.login input[type=text],.login input[type=password]{font:inherit;padding:9px 11px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)}
.login .rm{flex-direction:row;align-items:center;gap:8px}
.login button{font:inherit;cursor:pointer;border:0;background:var(--ink);color:var(--bg);border-radius:8px;padding:10px 14px;font-weight:600}
.login button:disabled{opacity:.6;cursor:wait}
.login .msg{min-height:1.4em;margin:0;color:var(--bad);font-size:13.5px}
.login .fine{margin:0;color:var(--muted);font-size:12.5px}
.logout{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--surface);color:var(--ink-2);border-radius:8px;padding:6px 12px}
'''
rep('.empty{padding:40px 16px;text-align:center;color:var(--muted)}',
    '.empty{padding:40px 16px;text-align:center;color:var(--muted)}' + LOGIN_CSS)

# ---- Planung-Reiter entfernen, Abmelden-Knopf in den Kopf
rep('    <button role="tab" data-t="planung">Planung</button>\n', '')
rep('''        <label for="to">bis</label><input type="date" id="to">
      </div>''', '''        <label for="to">bis</label><input type="date" id="to">
      </div>
      <button type="button" class="logout" id="logout">Abmelden</button>''')
rep('<main id="view"><div class="empty">Daten werden geladen …</div></main>',
    '<main id="view"><div class="empty">Wird geladen …</div></main>')

# ---- Gastro: keine Personaldetails
rep("""      kpi('Trinkgeld',eur(sumF(rows,'gastro.trinkgeld'),2),'')+
      kpi('Interner Verbrauch',eur(sumF(rows,'gastro.intern_netto'),2),'Personal, Besprechung, Bruch …')+`</div>`;""",
    """`</div>`;""")
rep("""    h+=`<div class="grid2"><div class="panel"><h2>Bediener</h2><p class="sub">Umsatz ohne interne Konten, brutto</p>${hbars(sumObj(rows,'gastro.staff'),'--ink-2')}</div>
      <div class="panel"><h2>Zahlungsarten</h2><p class="sub">brutto</p>${hbars(sumObj(rows,'gastro.zahlung'),'--ink-2')}
      <h2 style="margin-top:18px">Interne Konten</h2><p class="sub">netto</p>${hbars(sumObj(rows,'gastro.intern'),'--muted',v=>eur(v,2))}</div></div>`;""",
    """    h+=`<div class="panel"><h2>Zahlungsarten</h2><p class="sub">brutto</p>${hbars(sumObj(rows,'gastro.zahlung'),'--ink-2')}</div>`;""")

# ---- Hotel: keine Eingabe der Zimmeranzahl
rep("""     <div class="panel"><h2>Zimmernächte pro Tag</h2><p class="sub">${rooms?rooms+' Zimmer hinterlegt':'Zimmeranzahl eintragen, dann wird die Auslastung berechnet'}</p><div class="chart" id="c2"></div>
     <div class="cfg" style="margin-top:10px"><label for="rooms">Zimmer gesamt</label><input id="rooms" type="number" min="1" max="500" value="${rooms||''}"><button id="saveRooms">Speichern</button><span id="roomsMsg"></span></div></div></div>`;""",
    """     <div class="panel"><h2>Zimmernächte pro Tag</h2><p class="sub">${rooms?rooms+' Zimmer':'Alle Zimmernächte'}</p><div class="chart" id="c2"></div></div></div>`;""")
rep("""  $('#saveRooms').onclick=async()=>{const v=parseInt($('#rooms').value,10),m=$('#roomsMsg');if(!(v>0)){m.textContent='Bitte eine Zahl eingeben.';return}
    try{await DB.doc('config/betrieb').set(Object.assign({},CFG,{zimmer:v}));m.textContent='Gespeichert.'}catch(e){m.textContent='Speichern nicht möglich ('+(e.code||'Fehler')+').'}};
""", '')

# ---- Wochen-Controlling: kein „Planung bearbeiten“
rep("""<button type="button" class="btn" id="toPlan">Planung bearbeiten</button>""", '')
rep("""  $('#toPlan').onclick=()=>{tab='planung';try{history.replaceState(null,'','#planung')}catch(_){};render()};
""", '')
rep("""const h0=(location.hash||'').slice(1); if(['gastro','shop','hotel','uebersicht','controlling','planung'].includes(h0)) tab=h0;""",
    """const h0=(location.hash||'').slice(1); if(['gastro','shop','hotel','uebersicht','controlling'].includes(h0)) tab=h0;""")

# ---- Datenquelle: verschlüsselte Datei statt Claude-Datenbank
start = h.index("(async()=>{\n  DB=await (window.claude")
end = h.index("})();\n})();\n</script>", start)
LOADER = r"""const b64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const ub64=a=>btoa(String.fromCharCode(...new Uint8Array(a)));
const te=new TextEncoder();
const RK='dokl-cockpit-session';
let ENC=null;
function store(){try{return localStorage}catch(_){return null}}
async function uidOf(name){const d=await crypto.subtle.digest('SHA-256',te.encode('dokl-cockpit:'+name.trim().toLowerCase()));return [...new Uint8Array(d)].map(x=>x.toString(16).padStart(2,'0')).join('').slice(0,32)}
async function fetchEnc(){const r=await fetch('data.enc.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('Datei nicht erreichbar ('+r.status+')');return r.json()}
async function unwrap(e,name,pw){
  const ent=e.keys[await uidOf(name)];if(!ent)return null;
  const base=await crypto.subtle.importKey('raw',te.encode(pw),'PBKDF2',false,['deriveKey']);
  const kek=await crypto.subtle.deriveKey({name:'PBKDF2',salt:b64(ent.salt),iterations:e.kdf.iter,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['decrypt']);
  try{return new Uint8Array(await crypto.subtle.decrypt({name:'AES-GCM',iv:b64(ent.iv)},kek,b64(ent.wk)))}catch(_){return null}
}
async function openData(e,raw){
  const k=await crypto.subtle.importKey('raw',raw,'AES-GCM',false,['decrypt']);
  const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64(e.iv)},k,b64(e.ct));
  const txt=await new Response(new Blob([plain]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
  return JSON.parse(txt);
}
function show(D){
  document.body.classList.remove('locked');
  DAYS=(D.tage||[]).slice().sort((a,b)=>a.datum<b.datum?-1:1);BY={};DAYS.forEach(d=>BY[d.datum]=d);
  WEEKS={};(D.wochen||[]).forEach(x=>WEEKS[`${x.jahr}-${String(x.kw).padStart(2,'0')}`]=x);
  CFG=D.betrieb||{};ZIELE=Object.assign({},DEF_ZIELE,D.ziele||{});
  (D.plan||[]).forEach(x=>{if(x&&x.jahr)PLANS[x.jahr]=x});
  if(!DAYS.length){$('#view').innerHTML='<div class="panel empty">Noch keine Tagesdaten vorhanden.</div>';return}
  if(!cur||!BY[cur]) cur=DAYS[DAYS.length-1].datum;
  render();
}
function loginForm(msg){
  document.body.classList.add('locked');
  $('#logout').hidden=true;
  $('#view').innerHTML=`<form class="panel login" id="lf" autocomplete="on"><h2>Gesellschafter-Zugang</h2>
    <label>Benutzername<input type="text" id="lu" autocomplete="username" autocapitalize="none" spellcheck="false" required></label>
    <label>Passwort<input type="password" id="lp" autocomplete="current-password" required></label>
    <label class="rm"><input type="checkbox" id="lr">Auf diesem Gerät angemeldet bleiben</label>
    <button type="submit" id="lb">Anmelden</button><p class="msg" id="lm">${msg?esc(msg):''}</p>
    <p class="fine">Die Zahlen werden erst in deinem Browser mit deinem Passwort entschlüsselt.</p></form>`;
  $('#lf').onsubmit=async ev=>{ev.preventDefault();const b=$('#lb'),m=$('#lm');b.disabled=true;m.textContent='';b.textContent='Wird entschlüsselt …';
    try{
      ENC=ENC||await fetchEnc();
      const raw=await unwrap(ENC,$('#lu').value,$('#lp').value);
      if(!raw){m.textContent='Benutzername oder Passwort stimmt nicht.';return}
      const D=await openData(ENC,raw);
      const s=store();if(s){try{if($('#lr').checked)s.setItem(RK,JSON.stringify({v:ENC.kv,k:ub64(raw)}));else s.removeItem(RK)}catch(_){}}
      $('#logout').hidden=false;show(D);
    }catch(e){m.textContent='Fehler beim Laden: '+(e.message||e)}
    finally{b.disabled=false;b.textContent='Anmelden'}
  };
  setTimeout(()=>{const u=$('#lu');if(u)u.focus()},50);
}
$('#logout').onclick=()=>{const s=store();if(s){try{s.removeItem(RK)}catch(_){}}DAYS=[];BY={};loginForm('Abgemeldet.')};
(async()=>{
  document.body.classList.add('locked');
  try{ENC=await fetchEnc()}catch(e){$('#view').innerHTML='<div class="panel empty">Daten konnten nicht geladen werden. '+esc(e.message||'')+'</div>';return}
  const s=store();let saved=null;if(s){try{saved=JSON.parse(s.getItem(RK)||'null')}catch(_){}}
  if(saved&&saved.k){try{const D=await openData(ENC,b64(saved.k));$('#logout').hidden=false;show(D);return}catch(_){try{s.removeItem(RK)}catch(__){}}}
  loginForm(saved?'Der Zugang wurde erneuert. Bitte neu anmelden.':'');
"""
h = h[:start] + LOADER + h[end:]
rep("let mode='tag',cur=null,rFrom=null,rTo=null,tab='uebersicht',DB=null;",
    "let mode='tag',cur=null,rFrom=null,rTo=null,tab='uebersicht';")

rep("try{await DB.doc('plan/'+PY).set(doc);PLANS[PY]=doc;dirty=false;","try{throw {code:'nur lesen'};")
# Planungs-Code bleibt als totes Gerüst drin (wird nie aufgerufen), DB-Zugriffe dürfen aber nicht mehr vorkommen
for bad in ('DB.doc', 'DB.collection', 'window.claude', 'gastro.staff', 'gastro.trinkgeld', 'gastro.intern'):
    if bad in h:
        raise SystemExit('Rest gefunden: ' + bad)
pathlib.Path(dst).write_text(h, encoding='utf-8')
print('geschrieben', dst, len(h), 'Zeichen')
