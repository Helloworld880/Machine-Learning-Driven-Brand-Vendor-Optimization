# Vendor Insight 360 - Production Refactor

Vendor Insight 360 is now an API-driven vendor analytics platform with a decoupled architecture:
FastAPI backend, PostgreSQL data layer, modular service logic, ML risk prediction, ETL pipeline, and Streamlit frontend that consumes APIs.

## Architecture

```text
                        +----------------------+
                        |    Streamlit UI      |
                        |      app/app.py      |
                        +----------+-----------+
                                   |
                                   v
                        +----------------------+
                        |    FastAPI API       |
                        |     api/main.py      |
                        +----------+-----------+
                                   |
                        +----------+-----------+
                        |    Service Layer     |
                        | services/vendor_...  |
                        +----------+-----------+
                                   |
                  +----------------+----------------+
                  |                                 |
                  v                                 v
        +---------------------+           +---------------------+
        |  PostgreSQL Access  |           |     ML Model        |
        |  database/*.py      |           |   models/model.py   |
        +----------+----------+           +---------------------+
                   |
                   v
           +---------------+
           | PostgreSQL DB |
           +---------------+
                   ^
                   |
           +-------+-------+
           | ETL Pipeline  |
           | pipeline/*.py |
           +---------------+
```

## Project Structure

```text
vendor-insight-360/
├── app/
│   └── app.py
├── api/
│   └── main.py
├── services/
│   └── vendor_service.py
├── database/
│   ├── db.py
│   └── queries.py
├── models/
│   └── model.py
├── pipeline/
│   └── update_data.py
├── config/
│   └── settings.py
├── utils/
├── requirements.txt
├── Dockerfile
└── .env
```

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn
- Streamlit
- PostgreSQL + SQLAlchemy + pandas
- scikit-learn (RandomForest)
- JWT auth (`python-jose`)
- Docker

## Core API Endpoints

- `GET /` - health message
- `POST /login` - JWT token generation
- `GET /vendors` - vendor KPI data (protected)
- `GET /vendors/performance` - leaderboard + alerts (protected)
- `GET /vendors/performance/export` - CSV export (protected)

## KPI & Analytics

Service layer computes:

- `performance_score = delivery_rate*0.4 + quality_score*0.3 + cost_efficiency*0.3`
- `on_time_rate`
- `cost_variance`
- `reliability`
- ML `risk_prediction` (`good` / `risky`)

## Advanced Features Included

- Vendor leaderboard ranking (`rank`)
- Low-performing vendor alert flag (`low_performance_alert`)
- CSV export endpoint for performance reports

## Configuration

Create `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/vendor_insight
SECRET_KEY=replace-with-strong-secret
API_BASE_URL=http://localhost:8000
ACCESS_TOKEN_EXPIRE_MINUTES=120
LOG_LEVEL=INFO
```

## Local Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run ETL to load source data into PostgreSQL:

```bash
python pipeline/update_data.py
```

3. Start API:

```bash
uvicorn api.main:app --reload
```

4. Start frontend:

```bash
streamlit run app/app.py
```

## Docker Deployment

Build and run:

```bash
docker build -t vendor-insight-360 .
docker run --env-file .env -p 8000:8000 vendor-insight-360
```

## Production Notes

- Replace demo credentials in `api/main.py` with real user persistence.
- Use managed PostgreSQL and secure `SECRET_KEY`.
- Add migrations (Alembic) and CI/CD checks for production rollout.
