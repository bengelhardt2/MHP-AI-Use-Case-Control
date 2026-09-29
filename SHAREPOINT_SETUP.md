# SharePoint-Setup für MHP AI Control Dashboard

## Übersicht

Das Dashboard speichert den gemeinsamen Zustand über zwei Power-Automate-Flows
in einer SharePoint-Liste. Du brauchst dafür nur Microsoft 365 — kein Azure.

```
Browser (HTML-Datei in SharePoint)
    │
    ├─► Flow 1 (GET)  – Zustand lesen   ──► SharePoint-Liste
    └─► Flow 2 (SAVE) – Zustand schreiben ──► SharePoint-Liste
```

---

## Schritt 1 · SharePoint-Liste anlegen

1. Öffne deine SharePoint-Site
2. **Site contents → New → List → Blank list**
3. Name: `MHP AI Control State`
4. Füge diese zwei Spalten hinzu *(+ Add column)*:

| Spaltenname | Typ | Einstellung |
|---|---|---|
| `StateJson` | Multiple lines of text | Plain text, unbegrenzt |
| `UpdatedAt` | Single line of text | – |

5. Erstelle **genau einen Listeneintrag** (New item):
   - Title: `dashboard`
   - StateJson: `{}`
   - UpdatedAt: *(leer lassen)*

---

## Schritt 2 · Flow 1: Zustand lesen (GET)

**make.powerautomate.com → Create → Instant cloud flow**

| Schritt | Einstellung |
|---|---|
| Trigger | **When an HTTP request is received** |
| Method | GET |

### Actions hinzufügen:

**Action 1 – Get item (SharePoint)**
- Site Address: *(deine SharePoint-Site)*
- List Name: `MHP AI Control State`
- Id: `1`

**Action 2 – Response**
```
Status Code:  200
Headers:
  Content-Type: application/json
  Access-Control-Allow-Origin: *

Body:
{
  "state": @{if(empty(outputs('Get_item')?['body/StateJson']), '{}', outputs('Get_item')?['body/StateJson'])},
  "updatedAt": @{outputs('Get_item')?['body/UpdatedAt']}
}
```

> ⚠️ Wichtig: Den Body oben als **Expression** eingeben, nicht als Text.
> In Power Automate: In das Body-Feld klicken → Switch to "Code view" → einfügen.

Speichern → **HTTP POST URL** kopieren → das ist deine **GET-Flow-URL**.

---

## Schritt 3 · Flow 2: Zustand speichern (SAVE)

**make.powerautomate.com → Create → Instant cloud flow**

| Schritt | Einstellung |
|---|---|
| Trigger | **When an HTTP request is received** |
| Method | POST |
| Request Body JSON Schema | siehe unten |

**JSON Schema für den Trigger:**
```json
{
  "type": "object",
  "properties": {
    "state": { "type": "object" },
    "baseUpdatedAt": { "type": "string" }
  }
}
```

### Actions hinzufügen:

**Action 1 – Initialize variable** `varNow`
- Type: String
- Value: `@{utcNow()}`

**Action 2 – Get item (SharePoint)**
- Site Address: *(deine SharePoint-Site)*
- List Name: `MHP AI Control State`
- Id: `1`

**Action 3 – Condition** (Konflikt prüfen)
```
AND
  triggerBody()?['baseUpdatedAt']  is not equal to  empty
  outputs('Get_item')?['body/UpdatedAt']  is not equal to  empty
  outputs('Get_item')?['body/UpdatedAt']  is not equal to  triggerBody()?['baseUpdatedAt']
```

**If YES (Konflikt):**
- Action: **Response**
  - Status Code: `409`
  - Body: `{"error": "conflict"}`
  - Header: `Access-Control-Allow-Origin: *`

**If NO (kein Konflikt):**
- Action 1: **Update item (SharePoint)**
  - Site: *(deine SharePoint-Site)*
  - List: `MHP AI Control State`
  - Id: `1`
  - StateJson: `@{string(triggerBody()?['state'])}`
  - UpdatedAt: `@{variables('varNow')}`
- Action 2: **Response**
  - Status Code: `200`
  - Body: `{"updatedAt": "@{variables('varNow')}"}`
  - Header: `Access-Control-Allow-Origin: *`

Speichern → **HTTP POST URL** kopieren → das ist deine **SAVE-Flow-URL**.

---

## Schritt 4 · URLs ins Dashboard eintragen

Öffne `mhp-ai-control_3.html` in einem Text-Editor, suche nach:

```javascript
const REMOTE_GET_ENDPOINT  = "HIER_GET_FLOW_URL_EINSETZEN";
const REMOTE_PUT_ENDPOINT  = "HIER_SAVE_FLOW_URL_EINSETZEN";
```

Ersetze die Platzhalter durch deine kopierten Flow-URLs:

```javascript
const REMOTE_GET_ENDPOINT  = "https://prod-xx.westeurope.logic.azure.com/...";
const REMOTE_PUT_ENDPOINT  = "https://prod-xx.westeurope.logic.azure.com/...";
```

---

## Schritt 5 · HTML-Datei in SharePoint hochladen

1. Öffne deine SharePoint-Site
2. Gehe zu einer **Dokumentenbibliothek** (z. B. „Documents")
3. **Upload → Files** → `mhp-ai-control_3.html` auswählen
4. Rechtsklick auf die Datei → **Copy link**
5. Den Link mit Kollegen teilen

> 💡 Tipp: Den Link direkt im Browser öffnen (nicht als SharePoint-Seite einbetten).
> Die URL sollte auf `.../mhp-ai-control_3.html` enden.

---

## Workflow für alle Beteiligten

| Person | Aktion |
|---|---|
| **Kollege** | Link öffnen → mit MHP-Account anmelden → Daten befüllen → alles speichert automatisch |
| **Du** | Link öffnen → siehst den aktuellen Stand aller → weiterarbeiten |

Änderungen werden automatisch alle ~1,2 Sekunden nach SharePoint synchronisiert.
Alle 30 Sekunden prüft das Dashboard, ob jemand anderes etwas geändert hat.
