# AI Lorekeeper

**Your Life, Synthesized.**

AI Lorekeeper is a personal memory synthesis engine. Upload fragments of your digital life — chat exports, journal entries, screenshots, photos — and Gemma 4 transforms them into structured narrative: story arcs, recurring themes, emotional patterns, and mindset shifts.

Think Spotify Wrapped, but for your actual life.

Built for the **Gemma 4 Challenge — Build Track**.

---

## What It Does

1. **Upload your data** — TXT, PDF, MD, JSON, CSV, and images (JPG, PNG, WebP)
2. **Tag with context** — source (Journal, WhatsApp, Notes, etc.) and time period
3. **Run Synthesis** — AI analyzes everything chronologically and generates structured lore
4. **Explore your lore** — view narrative essays, story arcs, recurring people, mindset shifts, identity contradictions, and more
5. **Track evolution** — every synthesis creates a permanent snapshot; watch your lore grow over time

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy (async) |
| File Storage | Local filesystem |
| Auth | JWT (python-jose + bcrypt) |
| PDF Extraction | PyMuPDF |
| AI Inference | Gemma 4 via Google AI API |
| Output Validation | Pydantic |

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (local or remote)

### 1. Clone and set up the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure the environment

```bash
cp .env.example .env
# Edit .env with your database URL and Gemma API key
```

Required environment variables:
- `DATABASE_URL` — PostgreSQL connection string (async)
- `JWT_SECRET` — a long random string for token signing
- `GEMMA_API_KEY` — your Google AI API key (optional — app works with fallback data for demo)

### 3. Create the database

```bash
createdb lorekeeper
# Or via psql: CREATE DATABASE lorekeeper;
```

### 4. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Auto-generated docs at `http://localhost:8000/docs`.

### 5. Set up the frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

## API Endpoints

### Auth
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Sign in
- `DELETE /api/auth/account` — Delete account and all data

### Files
- `POST /api/files/upload` — Upload a file (multipart)
- `GET /api/files/` — List all files
- `DELETE /api/files/{id}` — Delete a file

### Synthesis
- `POST /api/synthesis/trigger` — Run synthesis on all (or selected) files
- `GET /api/synthesis/runs` — List synthesis runs
- `GET /api/synthesis/snapshots` — List lore snapshots
- `GET /api/synthesis/snapshots/{id}` — Get full lore detail

## Gemma 4 Output Schema

Every synthesis call returns a structured JSON object:

```json
{
  "the_sentence": "A haunting concluding line (max 30 words)",
  "narrative": "Prose essay, 300-500 words, second person",
  "story_arcs": [{ "title": "...", "description": "..." }],
  "recurring_people": [{ "identifier": "...", "context": "..." }],
  "defining_moments": [{ "moment": "...", "significance": "..." }],
  "mindset_shifts": [{ "from": "...", "to": "...", "evidence": "...", "period": "..." }],
  "core_themes": ["..."],
  "identity_contradictions": [{ "observation": "...", "evidence": "...", "interpretation": "..." }]
}
```

## Project Structure

```
gemma/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   └── utils/               # Dependency injection
│   ├── uploaded_files/          # File storage directory
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── components/              # Reusable React components
│   ├── lib/                     # API client and types
│   └── package.json
└── README.md
```

## Demo

To see AI Lorekeeper in action:

1. Start backend and frontend
2. Register an account
3. Upload sample files (journal entries, chat exports, photos)
4. Click "Synthesize All"
5. Explore your lore snapshots
6. Upload more files and synthesize again to see lore evolution

Sample data is included in the `demo-data/` directory (journal entries, WhatsApp-style chat exports, and image descriptions).

## Deployment

### Backend (Railway / Render)
```bash
cd backend
docker build -t lorekeeper-backend .
# Deploy the Docker container to your platform of choice
```

### Frontend (Vercel)
```bash
cd frontend
npx vercel --prod
```

Set `NEXT_PUBLIC_API_URL` to your deployed backend URL.

## License

MIT
