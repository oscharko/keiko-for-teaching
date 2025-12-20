# Keiko Development Standards

| Metadaten | Wert |
|-----------|------|
| **Version** | 1.1 |
| **Status** | Freigegeben |
| **Gültig ab** | 2025-01-01 |
| **Nächste Überprüfung** | 2025-07-01 |
| **Owner** | Platform Engineering Team |
| **Genehmigt durch** | Chief Technology Officer |

---

## Über dieses Dokument

### Zweck

Dieses Dokument definiert die verbindlichen architektonischen und operativen Standards für alle Azure Cloud-Native und AI-First Entwicklungen im Keiko-Ökosystem.

### Gültigkeitsbereich

Diese Standards gelten für:

- Alle neu entwickelten Services und Komponenten
- Alle wesentlichen Überarbeitungen bestehender Services
- Alle Infrastruktur-Deployments in Azure

### Terminologie (RFC 2119)

Die Schlüsselwörter in diesem Dokument sind wie folgt zu interpretieren:

| Begriff | Bedeutung |
|---------|-----------|
| **MUSS** | Zwingende Anforderung. Keine Ausnahmen ohne formale Genehmigung. |
| **SOLL** | Starke Empfehlung. Abweichungen erfordern dokumentierte Begründung. |
| **KANN** | Optionale Empfehlung. Umsetzung nach eigenem Ermessen. |

---

## 1. Cloud-Native Azure Architektur & Governance

### 1.1 Infrastructure as Code (IaC)

#### Bicep & Deployment Stacks

Für neue Azure-Workloads **MUSS** Bicep mit Azure Deployment Stacks verwendet werden. Terraform ist nicht zulässig.

**Begründung:**

- Die Business Source License (BSL 1.1) schränkt seit August 2023 kommerzielle Nutzung in konkurrierenden Angeboten ein.
- Das Resources Under Management (RUM) Preismodell von Terraform Cloud bestraft granulare Microservices-Architekturen finanziell (ca. $0.10 pro Ressource/Monat nach 500 Frei-Ressourcen).
- Terraform erkennt Drift nur reaktiv, während Deployment Stacks präventiven Schutz auf ARM-Ebene bieten.

#### Governance-Modus

Deployment Stacks **MÜSSEN** mit folgendem Governance-Modus konfiguriert werden:

```bicep
denySettingsMode: 'denyWriteAndDelete'
```

Dies sperrt Ressourcen auf ARM-Ebene gegen manuelle Portal-Änderungen und erzwingt Änderungen ausschließlich via Code.

| Wert | Beschreibung |
|------|--------------|
| `'none'` | Keine Einschränkungen |
| `'denyDelete'` | Löschen blockiert |
| `'denyWriteAndDelete'` | Ändern und Löschen blockiert (**Standard**) |

#### Azure Verified Modules (AVM)

Eigener IaC-Code **SOLL** nur Business-Logik und Orchestrierung enthalten. Für Standard-Ressourcen (AKS, Key Vault, Storage, etc.) **MÜSSEN** offizielle Azure Verified Modules komponiert werden, um Microsoft Best Practices zu erben und Wartungsaufwand zu reduzieren.

### 1.2 Runtime & Skalierung (Azure Container Apps)

#### Sidecar-Strategie (Dapr)

Dapr bietet leistungsfähige Abstraktionen, verursacht jedoch zusätzlichen Ressourcenverbrauch (Sidecar-Overhead).

| Service-Typ | Dapr-Status | Begründung |
|-------------|-------------|------------|
| Service-to-Service | **MUSS** aktiviert sein | mTLS, Tracing, Resiliency |
| Worker/Transformer | **SOLL** deaktiviert sein | Keine externe Kommunikation, Ressourceneinsparung |

#### Intelligentes Scaling (KEDA)

Die Skalierung von AI-Workloads **DARF NICHT** auf CPU/RAM basieren.

- KEDA Scaler (Service Bus, Event Hubs) **MÜSSEN** verwendet werden.
- **Lag-Based Scaling:** Die Skalierung **SOLL** auf der geschätzten Verarbeitungszeit (Lag) basieren, um Pipeline-Verstopfungen zu vermeiden.
- **Scale to Zero:** `minReplicas: 0` **MUSS** für Dev-Umgebungen und asynchrone Worker konfiguriert werden.

### 1.3 Networking & Security

#### Outbound Restrictions

Compute-Ressourcen (ACA, Functions) **MÜSSEN** standardmäßig jeglichen ausgehenden Traffic blockieren (Deny All). Allow-Listing erfolgt ausschließlich für:

- Private Endpoints der eigenen Azure AI Services
- Explizit genehmigte FQDNs

#### Shadow AI Prevention

Azure Policies **MÜSSEN** implementiert werden, die das Deployment von nicht-sanktionierten Modellen (z.B. öffentliche Previews) oder nicht-konformen Regionen blockieren.

---

## 2. AI-First Architektur: Foundry, RAG & Agents

### 2.1 RAG Architektur & Vektorisierung

#### Integrated Vectorization

Client-Services **DÜRFEN NICHT** Embeddings selbst generieren. Stattdessen:

1. Push von Rohtext an Azure AI Search
2. Server-seitige Vektorisierung via Indexer und Skillsets

**Begründung:** Vermeidung von Latenz und Komplexität im Client.

#### SKU-Restriktion

Die Nutzung des S3 High Density (S3 HD) Modus **IST NICHT ZULÄSSIG**, wenn Integrated Vectorization genutzt wird.

**Begründung:** S3 HD unterstützt technisch keine Indexer und erfordert ausschließlich Push-basierte Datenaufnahme via REST API.

#### Semantic Ranker

Der Semantic Ranker **SOLL** selektiv nur für die finale Antwort-Generierung eingesetzt werden.

**Begründung:** Vermeidung von Kostenexplosionen bei iterativen Agenten-Loops.

### 2.2 Agentic State & Disaster Recovery

#### State Management

Der interne State des Azure AI Foundry Agent Service ist flüchtig und bietet kein Point-in-Time Restore.

- Konversationshistorie **MUSS** in Azure Cosmos DB persistiert werden.
- Agenten-Kontexte **MÜSSEN** in Azure Cosmos DB persistiert werden.

#### Recovery Pipeline

Da Azure AI Search Indizes keine nativen Backups unterstützen, **MUSS** eine Re-Hydration Pipeline existieren (z.B. Azure Batch), die den Index aus der Source of Truth neu aufbauen kann.

---

## 3. Identität & Authentifizierung

### 3.1 Customer Identity (CIAM)

#### Azure AD B2C

Die Nutzung von Azure AD B2C **IST NICHT ZULÄSSIG** für neue Services.

**Begründung:** Der Dienst ist seit 1. Mai 2025 für Neukunden nicht mehr verfügbar. Bestehende Kunden werden bis mindestens Mai 2030 unterstützt.

#### Microsoft Entra External ID

Migration zu Microsoft Entra External ID **MUSS** erfolgen.

> **Hinweis:** Custom Policies (XML) werden in External ID nicht unterstützt. Stattdessen User Flows mit Custom Authentication Extensions verwenden.

### 3.2 Token Enrichment & Performance

Custom Claims Provider (API-Hooks) **DÜRFEN NICHT** auf Consumption Plan Functions laufen.

| Zulässige Compute-Optionen | Konfiguration |
|---------------------------|---------------|
| Premium Functions | Standard |
| Container Apps | `minReplicas: 1` oder höher |

**Begründung:** Vermeidung von Login-Latenzen oder Timeouts durch Cold Starts.

---

## 4. Python Toolchain

### 4.1 Package & Version Management

#### uv als Standard-Tooling

**uv** (by Astral) **MUSS** als einziges Dependency-Management-Tool verwendet werden.

| Ersetzt | Durch |
|---------|-------|
| pip | `uv pip` |
| poetry | `uv add`, `uv sync` |
| pyenv | `uv python install` |
| pipx | `uv tool` |
| virtualenv | `uv venv` |

**Begründung:** 10-100x schnellere Dependency-Auflösung als pip, signifikante Reduktion der CI/CD-Build-Zeiten. Produktionsreif seit 2024.

#### Runtime-Konsistenz

Python-Versionen **MÜSSEN** via `uv` verwaltet werden:

```bash
uv python install 3.12
```

Eine `.python-version` Datei **MUSS** im Repository-Root existieren, um bit-genaue Reproduzierbarkeit zwischen lokaler Entwicklung und CI-Umgebung sicherzustellen.

### 4.2 Observability & Privacy

#### LLM Tracing

**Pydantic Logfire** **MUSS** für die Visualisierung von LLM-Traces eingesetzt werden.

Funktionsumfang:

- Chain-Visualisierung
- Tool Call Tracking
- Token-Tracking
- Kostenanalyse
- OpenTelemetry-native Integration

#### PII Scrubbing

Logfire **MUSS** in Kombination mit einem lokalen OpenTelemetry Collector konfiguriert werden.

**Anforderung:** Sensible Daten (PII) in Prompts **MÜSSEN** maskiert werden, **bevor** die Daten das Netzwerk verlassen.

---

## 5. AI Coding Agent Instructions

Dieser Block **SOLL** in die Custom Instructions von AI Coding Agents (Cursor, GitHub Copilot, Windsurf, etc.) kopiert werden:

```markdown
### KEIKO CODING STANDARDS (ENFORCED)

1. **IaC Generation**:
   - ALWAYS use **Bicep** with **Azure Deployment Stacks**.
   - Set `denySettingsMode: 'denyWriteAndDelete'` in stack configuration.
   - Search for **Azure Verified Modules (AVM)** before writing custom resource code.
   - DO NOT use Terraform.

2. **Python & Tooling**:
   - ALWAYS use `uv` commands (e.g., `uv add`, `uv sync`) for dependency management.
   - DO NOT suggest `pip install` or `poetry`.

3. **AI Architecture**:
   - For RAG, define an **Azure AI Search Indexer** with a Skillset for **Integrated Vectorization**.
   - DO NOT generate client-side code that calls OpenAI Embeddings API directly.
   - For Custom Auth Extensions (Entra), ensure the backing compute has `minReplicas: 1` (No Cold Starts).

4. **Network Security**:
   - When defining Container Apps or Functions, ALWAYS allow outbound traffic ONLY to specific Private Endpoints (Deny All by default).
```

---

## 6. Ausnahmen & Eskalation

### 6.1 Ausnahmeprozess

Abweichungen von diesen Standards **KÖNNEN** in begründeten Ausnahmefällen genehmigt werden.

**Voraussetzungen:**

1. Schriftliche Begründung mit technischer Analyse
2. Risikobewertung
3. Genehmigung durch den Technical Lead
4. Dokumentation im Architecture Decision Record (ADR)

### 6.2 Eskalationspfad

| Stufe | Genehmiger | Gültigkeitsdauer |
|-------|------------|------------------|
| 1 | Technical Lead | 30 Tage |
| 2 | Principal Engineer | 90 Tage |
| 3 | CTO | Unbefristet |

---

## Änderungshistorie

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|------------|
| 1.0 | 2024-12-01 | Platform Engineering | Initiale Version |
| 1.1 | 2025-01-01 | Platform Engineering | RFC 2119 Terminologie, Ausnahmeprozess, Strukturoptimierung |
