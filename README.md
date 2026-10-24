# Dokl Cockpit · Gesellschafter

Verschlüsselte, schreibgeschützte Version des Dokl Tagescockpits für die Gesellschafter.
Die Seite liegt in `docs/` und wird über GitHub Pages ausgeliefert.

- `docs/index.html` – das Cockpit (ohne Personaldetails, ohne Planungs-Eingabe)
- `docs/data.enc.json` – die Zahlen, AES-256-GCM-verschlüsselt. Jeder Gesellschafter hat einen eigenen
  Benutzernamen und ein eigenes Passwort (PBKDF2-SHA-256, 600 000 Runden), mit dem sein Browser den Datenschlüssel entschlüsselt.
- `tools/build_site.py` – erzeugt `docs/index.html` aus dem Claude-Cockpit
- `tools/crypt.mjs` – Schlüssel verwalten und Daten verschlüsseln (Node ≥ 18)

Die Schlüssel (Datenschlüssel, Passwörter) liegen **nicht** hier, sondern privat bei David
im Claude-Artifact „Dokl Cockpit-Zugänge“. Die tägliche Claude-Aufgabe aktualisiert `docs/data.enc.json`.

Nicht enthalten, auch nicht verschlüsselt: Umsätze je Bediener, Trinkgeld, interne Konten/Personalverbrauch.
