# Dokl Cockpit · Gesellschafter – Hinweise für Claude Code

Dieses Repository ist die **verschlüsselte, schreibgeschützte Gesellschafter-Version** des Dokl Tagescockpits
(Rasthaus „Zum Dokl“, Hofstätten). Es wird über **GitHub Pages aus `main` / Ordner `docs/`** ausgeliefert.
Ansprechpartner: David Trummer.

## Aufbau
- `docs/index.html` – Cockpit-Seite mit Login (Benutzername + Passwort). Erzeugt aus dem Claude-Cockpit mit `tools/build_site.py`. Nicht von Hand groß umbauen; Änderungen am Cockpit über `build_site.py` nachziehen.
- `docs/data.enc.json` – die Zahlen, AES-256-GCM-verschlüsselt (gzip-JSON). Wird **täglich automatisch** von einer geplanten Claude-Aufgabe (Cowork, Microsoft-365-Connector) neu geschrieben und gepusht. **Nie von Hand ändern, nie löschen.**
- `docs/.nojekyll` – muss bleiben, sonst verarbeitet GitHub Pages die Dateien mit Jekyll.
- `tools/crypt.mjs` – Schlüssel verwalten und Daten verschlüsseln (Node ≥ 18, keine Abhängigkeiten). Aufrufe stehen im Dateikopf.
- `tools/build_site.py` – erzeugt `docs/index.html` aus der Datei `Dokl_Tagescockpit.html` (Original-Cockpit aus Claude).

## Sicherheitsregeln (verbindlich)
1. **Keine Geheimnisse ins Repository.** Datenschlüssel, Passwörter und GitHub-Tokens liegen ausschließlich privat bei David im Claude-Artifact „Dokl Cockpit-Zugänge“. Dateien wie `secrets*.json` oder `*schluessel*.json` sind per `.gitignore` gesperrt – diese Sperre nicht entfernen, nichts davon mit `git add -f` hinzufügen.
2. **Keine Klartext-Daten ins Repository**: keine Tagesberichte, keine DB-Exporte (`export/`), keine entschlüsselten JSON-Dateien, keine Screenshots mit Zahlen.
3. Personaldetails (Umsatz je Bediener, Trinkgeld, interne Konten/Personalverbrauch) dürfen in der Gesellschafter-Version **nicht** vorkommen – weder in `index.html` noch in den verschlüsselten Daten. `crypt.mjs` filtert sie (`gastro.staff`, `trinkgeld`, `intern`, `intern_netto`, `quelle`); diesen Filter nicht entfernen.
4. Die Git-Historie ist öffentlich. Wurde doch einmal ein Geheimnis committet: sofort David melden – Token widerrufen bzw. Datenschlüssel rotieren (`crypt.mjs rotate`), Historie bereinigen reicht nicht.
5. Keine Analyse-, Tracking- oder Fremd-Skripte einbauen. Einzige externe Quelle ist Google Fonts.

## Typische Aufgaben
- **Seite nach Cockpit-Änderung neu bauen:** `python3 tools/build_site.py <Dokl_Tagescockpit.html> docs/index.html`. Das Skript bricht ab, wenn eine Ersetzung nicht mehr greift – dann die Ersetzung in `build_site.py` an das neue Original anpassen, nicht die Prüfung abschalten. Danach lokal testen (siehe unten), committen, pushen.
- **Lokal testen:** `cd docs && python3 -m http.server 8765` und im Browser `http://localhost:8765` öffnen. Ohne gültigen Zugang erscheint nur das Login – das ist korrekt.
- **Benutzer anlegen/entziehen:** passiert nicht hier, sondern in Claude (Cowork) über das Zugänge-Artifact, weil dort die Schlüssel liegen.

## Commit-Stil
Kurze deutsche Commit-Messages, z. B. „Cockpit: Hotel-Reiter angepasst“. Automatische Daten-Commits heißen „Daten bis JJJJ-MM-TT“.
