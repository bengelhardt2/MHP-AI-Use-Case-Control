# MHP AI Control Dashboard

Gemeinsames Dashboard zur Verwaltung von KI-Use-Cases bei MHP.

---

## Schnellstart

```bash
python3 server.py
```

Browser öffnen: **http://localhost:8080**

> Voraussetzung: Python 3.9 oder neuer (auf macOS vorinstalliert).

---

## Kollaborativer Workflow

Alle Beteiligten arbeiten auf derselben `data/state.json` — über Git synchronisiert.

### 1 · Repo klonen (einmalig)

```bash
git clone https://github.com/bengelhardt2/MHP-AI-Use-Case-Control.git
cd MHP-AI-Use-Case-Control
```

### 2 · Aktuellen Stand holen

```bash
git pull
```

### 3 · Server starten und Dashboard befüllen

```bash
python3 server.py
```

Änderungen werden automatisch in `data/state.json` gespeichert.

### 4 · Änderungen ins Repo übertragen

```bash
git add data/state.json
git commit -m "Update: <kurze Beschreibung der Änderung>"
git push
```

### 5 · Änderungen von anderen übernehmen

```bash
git pull
```

Anschließend `python3 server.py` neu starten — der Server liest den neuen Stand ein.

---

## Hinweise

| Thema | Detail |
|-------|--------|
| Konflikt-Erkennung | Das Dashboard erkennt, wenn zwei Personen gleichzeitig schreiben, und zeigt eine Warnung. Dann einfach `git pull` und Server neu starten. |
| Offline-Modus | Ohne Server speichert das Dashboard im Browser-LocalStorage (nur lokal sichtbar). |
| Benutzerkennung | Als Name wird automatisch der Systemnutzer des Rechners verwendet. |
| Port | Standard ist 8080. Anderer Port: `PORT=9000 python3 server.py` |

---

## Dateistruktur

```
.
├── mhp-ai-control_3.html   ← Das Dashboard (Single-Page-App)
├── server.py               ← Lokaler HTTP-Server (Python, keine Abhängigkeiten)
├── data/
│   └── state.json          ← Gemeinsamer Zustand (wird in Git versioniert)
└── README.md
```
