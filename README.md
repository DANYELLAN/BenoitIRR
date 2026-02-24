# Benoit IRR Backend

Python/FastAPI backend for automating the pipe connector inspection workflow.

## What this backend includes

- ADP-based inspector login flow using SharePoint Employees list filters:
  - `Active == true`
  - `Branch == Ennis`
  - `Department in [Quality, Tubular]`
- Work order pull from AcumaticaDataStorage SharePoint list (`Production Operations`).
- Recipe lookup from QMS SharePoint (`InspectionRecipes`).
- Inspection submission workflow with:
  - shift/area/machine context from workstation + login time
  - pipe sequence tracking
  - pass/fail route to `COMPLETED`, reinspection queues, or `SCRAPPED`
  - NCR auto-creation and open/closed handling
- SQL persistence for inspection and NCR records.

## Configure

Create `.env`:

```env
CLIENT_SECRET=<azure-app-client-secret>
DATABASE_URL=postgresql+psycopg://postgres:B3n01tI4I9@localhost:8084/benoitirr
TENANT_ID=519943e3-a90d-49f1-a2a4-dd32f586c05f
CLIENT_ID=5520a688-ca19-493f-9050-f5c356fbeaff
```

If `DATABASE_URL` is not set, the app now defaults to your provided PostgreSQL connection.

## Install and run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000/api`

## Endpoints

- `GET /api/health`
- `POST /api/login`
- `GET /api/work-orders`
- `GET /api/recipes/{connection_name}`
- `POST /api/inspections`
- `GET /api/inspections`

## Notes on SharePoint fields

The Graph integration expects these column names in list item `fields` payloads:

- Employees: `ADPNumber`, `Title`, `Active`, `Branch`, `Department`
- InspectionRecipes: `Title`, `limits` (JSON dictionary or text JSON)

If your internal field names differ, map them in `app/services/sharepoint_service.py`.
