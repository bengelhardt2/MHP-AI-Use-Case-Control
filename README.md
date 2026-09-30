# MHP AI Control Dashboard

Gemeinsames Dashboard zur Verwaltung von KI-Use-Cases bei MHP.

**Dashboard:** https://bengelhardt2.github.io/MHP-AI-Use-Case-Control/

Einrichtung für neue Kolleg:innen: siehe Einrichtungsanleitung (PDF). Kurzfassung:
GitHub-Konto → Einladung zum Repo annehmen → Personal Access Token (classic, Scope `repo`) → Dashboard öffnen und Token eingeben.

---

## Architektur

```
Browser ── GitHub Pages (Branch main) ── index.html  (React-App, eine Datei)
   │
   └── GitHub REST API ── Branch data ── data/state.json  (gemeinsamer Stand)
```

| Baustein | Umsetzung |
|---|---|
| Frontend | `index.html` – React, Babel und Tailwind eingebettet, kein Build-Schritt |
| Hosting | GitHub Pages aus `main` |
| Datenhaltung | `data/state.json` auf Branch `data`. Getrennt von `main`, damit Speichern keinen Pages-Build auslöst |
| Identität & Rechte | Persönlicher GitHub-Token je Person. Lesen: jeder. Schreiben: Collaborators des Repos |
| Historie | Jede Speicherung ist ein Commit mit Autor und geänderten Bereichen → `git log data` |
| Audit | Use Cases, Deployments, Quellen und Retirement Log tragen `createdBy/At` und `updatedBy/At` |

### Gleichzeitiges Arbeiten

Jeder Browser merkt sich den zuletzt abgeglichenen Stand (Basis). Speichert jemand anderes zwischendurch,
lehnt GitHub die veraltete Version ab (HTTP 409). Das Dashboard lädt dann den neuen Stand, führt ihn per
Drei-Wege-Merge mit den eigenen Änderungen zusammen und speichert erneut – ohne Neuladen.

- Zusammengeführt wird pro Eintrag (über die `id`) und pro Feld.
- Nur wenn zwei Personen dasselbe Feld desselben Eintrags ändern, gewinnt die zuletzt speichernde.
- Legen zwei Personen gleichzeitig einen Eintrag mit derselben ID an, wird der zweite umnummeriert.
- Fremde Änderungen erscheinen nach spätestens 15 Sekunden (sofort beim Zurückwechseln in den Tab).
- Ohne Verbindung bleiben Änderungen im Browser und werden nachgereicht.

### Statusanzeige (oben rechts)

| Anzeige | Bedeutung |
|---|---|
| Gemeinsamer Stand | Verbunden, Änderungen werden geteilt |
| Speichert … | Übertragung läuft |
| Nur lesen | Kein Token, oder Einladung zum Repo noch nicht angenommen |
| Token ungültig | Token abgelaufen/widerrufen → „Anmelden“ |
| Nicht verbunden | Netzwerkproblem, Änderungen werden nachgereicht |

Klick auf den eigenen Namen meldet ab (Token wird aus dem Browser entfernt).

---

## Administration

Collaborator hinzufügen (Schreibrecht):

```bash
gh api repos/bengelhardt2/MHP-AI-Use-Case-Control/collaborators/GITHUB_USERNAME --method PUT --field permission=push
```

Oder im Browser: Repo → Settings → Collaborators → Add people → Role „Write“.

Wer hat was geändert:

```bash
git fetch origin data && git log --format='%ad  %s' --date=format:'%Y-%m-%d %H:%M' origin/data -- data/state.json
```

Stand wiederherstellen: ältere Version von `data/state.json` aus der Historie des Branches `data` zurückspielen,
oder im Dashboard eine zuvor gesicherte JSON-Datei über „Laden“ einspielen.

> Das Repo ist öffentlich. Keine personenbezogenen oder vertraulichen Daten eintragen.

---

## Lokale Entwicklung

```bash
python3 server.py
```

Öffnet das Dashboard unter http://localhost:8080 mit einem lokalen Backend (`.dev-data/state.json`,
nicht versioniert) – Tests verändern also nicht die echten Daten. Als andere Person testen:
`DEV_USER=anna python3 server.py`. Anderer Port: `PORT=9000 python3 server.py`.

Das Backend wird automatisch gewählt: auf `*.github.io` und bei `file://` GitHub, sonst `server.py`.

## Dateien

```
.
├── index.html   Dashboard (Single-Page-App)
├── server.py    Lokaler Entwicklungsserver, gleiche Schnittstelle wie Produktion
└── README.md
```
