# Riksdagen Dataplattform

En event-driven dataplattform som hämtar live-data från Riksdagens öppna API, streamar den genom Apache Kafka, lagrar i PostgreSQL och visualiserar i en Streamlit-dashboard.

## Arkitektur

```
Riksdagens API
      ↓
  Producers (hämtar data var 30 min)
      ↓
  Cleaners (rensar och strukturerar)
      ↓
    Kafka (buffrar meddelanden)
      ↓
  Consumer (läser och sparar)
      ↓
  PostgreSQL (lagrar permanent)
      ↓
  Streamlit Dashboard (visualiserar)
```

## Teknikstack

| Teknik | Användning |
|--------|-----------|
| Apache Kafka | Event streaming / meddelandekö |
| PostgreSQL | Relationsdatabas |
| Docker & Docker Compose | Container-orchestration |
| Python | Producers, consumer, cleaners |
| Streamlit | Dashboard / visualisering |
| httpx | Async HTTP-anrop mot Riksdagens API |
| Plotly | Interaktiva diagram |

## Projektstruktur

```
.
├── app/
│   └── dashboard.py          # Streamlit dashboard
├── cleaners/
│   ├── clean_anforanden.py   # Rensar anförande-data
│   ├── clean_dokument.py     # Rensar dokument-data
│   ├── clean_kalender.py     # Rensar kalender-data
│   ├── clean_ledamoter.py    # Rensar ledamöter-data
│   └── clean_voteringar.py   # Rensar voterings-data
├── config/
│   └── settings.py           # API-URLs och konfiguration
├── consumers/
│   └── consumer.py           # Kafka consumer → PostgreSQL
├── producers/
│   ├── anforanden_producer.py
│   ├── dokument_producer.py
│   ├── kalender_producer.py
│   ├── ledamoter_producer.py
│   └── voteringar_producer.py
├── services/
│   ├── kafka_producer.py     # Skickar meddelanden till Kafka
│   └── riksdag_api.py        # Hämtar data från Riksdagens API
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── pyproject.toml
```

## Databasschema

```sql
ledamoter:   id, namn, parti, valkrets
voteringar:  id, titel, punkt, riksmote, talare, parti, datum, rost, intressent_id
dokument:    id, titel, datum, typ, organ, parti, dok_url
kalender:    id, titel, start, slut, plats, kategori
anforanden:  id, talare, parti, text, intressent_id
```

> `intressent_id` kopplar ihop `ledamoter`, `voteringar` och `anforanden` — samma person i alla tabeller.

## Kom igång

### Krav
- Docker Desktop installerat
- Git

### Starta hela systemet

```bash
# Klona projektet
git clone https://github.com/DITT-ANVÄNDARNAMN/riksdagen-pipeline.git
cd riksdagen-pipeline

# Bygg och starta alla containers
cd docker
docker compose up -d --build
```

Öppna dashboarden på **http://localhost:8501**

### Starta om efter ändringar

```bash
cd docker
docker compose up -d --build
```

### Starta om specifik service

```bash
docker compose restart dashboard
docker compose restart consumer
docker compose restart producer_voteringar
```

## Kommandon

### Kolla att allt körs

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Kolla data i databasen

```bash
docker exec riksdagen_db psql -U user -d riksdagen -c "
SELECT 'ledamoter' AS tabell, COUNT(*) FROM ledamoter
UNION ALL SELECT 'voteringar', COUNT(*) FROM voteringar
UNION ALL SELECT 'dokument', COUNT(*) FROM dokument
UNION ALL SELECT 'kalender', COUNT(*) FROM kalender
UNION ALL SELECT 'anforanden', COUNT(*) FROM anforanden;"
```

### Kolla röster (Ja/Nej/Frånvarande)

```bash
docker exec riksdagen_db psql -U user -d riksdagen -c "
SELECT rost, COUNT(*) FROM voteringar GROUP BY rost;"
```

### Kolla senaste votering

```bash
docker exec riksdagen_db psql -U user -d riksdagen -c "
SELECT MAX(datum) FROM voteringar;"
```

### Kolla senaste dokument

```bash
docker exec riksdagen_db psql -U user -d riksdagen -c "
SELECT titel, datum FROM dokument ORDER BY datum DESC LIMIT 5;"
```

### Kolla loggar

```bash
# Consumer
docker logs docker-consumer-1 --tail 20

# En producer
docker logs docker-producer_voteringar-1 --tail 10
docker logs docker-producer_dokument-1 --tail 10
docker logs docker-producer_anforanden-1 --tail 10

# Dashboard
docker logs docker-dashboard-1 --tail 10
```

### Starta om med ny databas (radera all data)

```bash
cd docker
docker compose down
docker volume rm docker_postgres_data
docker compose up -d --build
```

### Återställa Kafka-offsets (läs om all data)

```bash
docker exec kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group riksdagen-group \
  --reset-offsets --to-earliest \
  --all-topics --execute
```

## Data som hämtas

| Datakälla | Uppdatering | Antal rader |
|-----------|------------|-------------|
| Ledamoter | Var 30 min | ~349 |
| Voteringar | Var 30 min | ~2500 (5 riksmöten) |
| Dokument | Var 30 min | Växer kontinuerligt |
| Kalender | Var 30 min | ~150 |
| Anföranden | Var 30 min | ~3000+ |

## Dashboard-funktioner

- **KPI-kort** — Antal rader per tabell i realtid
- **Partifördelning** — Stapeldiagram och cirkeldiagram
- **Röstfördelning** — Ja/Nej/Frånvarande per parti
- **Motionsjämförelse** — Välj en motion och jämför hur partierna röstade
- **Politiker-sökning** — Sök en ledamot och se rösthistorik och anföranden
- **Voteringar över tid** — Linjediagram från 2021-2026
- **Kommande händelser** — Kalender från Riksdagen
- **Senaste dokument** — Med klickbara länkar

## API-källor

- Voteringar: `https://data.riksdagen.se/voteringlista/`
- Anföranden: `https://data.riksdagen.se/anforandelista/`
- Dokument: `https://data.riksdagen.se/dokumentlista/`
- Kalender: `https://data.riksdagen.se/kalender/`
- Ledamoter: `https://data.riksdagen.se/personlista/`

