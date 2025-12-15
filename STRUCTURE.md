# Project Structure

This is a monorepo containing both backend and frontend for the Supply Chain Intelligence Dashboard.

## Directory Layout

```
Product X/
├── backend/                          # FastAPI backend server
│   ├── copilot_backend.py           # Main FastAPI application
│   ├── auth_db.py                   # Authentication & SQLite database
│   ├── intent_detector.py           # LLM intent detection
│   ├── query_engine.py              # CSV data query engine
│   ├── smart_query_engine.py        # Smart query parsing
│   ├── smart_query_engine_v2.py     # Enhanced query engine
│   ├── ai_providers_groq.py         # Groq LLM integration
│   ├── ai_providers_openai.py       # OpenAI LLM integration
│   ├── dataset.py                   # Dataset utilities
│   ├── data_enrichment.py           # Data enrichment functions
│   ├── llm_context.py               # LLM context management
│   ├── process_data.py              # Data processing utilities
│   ├── audit_bot.py                 # Audit functionality
│   ├── diagnose_issue.py            # Diagnostic tools
│   ├── requirements.txt             # Python dependencies
│   ├── shipment_data_1M.csv         # 1M shipment dataset
│   └── auth.db                      # SQLite authentication database
│
├── frontend/                         # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AICopilot.tsx       # Main dashboard page
│   │   │   ├── Login.tsx            # Authentication page
│   │   │   ├── InventoryManagement.tsx
│   │   │   ├── ShipmentDetails.tsx
│   │   │   ├── SupplyChainETA.tsx
│   │   │   └── PredictionsAnalytics.tsx
│   │   ├── components/
│   │   │   ├── AICopilotChat.tsx   # Chat component
│   │   │   ├── Sidebar.tsx         # Navigation sidebar
│   │   │   ├── Topbar.tsx          # Top navigation
│   │   │   └── ... (other components)
│   │   ├── utils/
│   │   │   ├── csvLoader.ts        # CSV loading utilities
│   │   │   ├── storage.ts          # Local storage utilities
│   │   ├── App.tsx                 # Root app component
│   │   └── main.tsx               # Entry point
│   ├── package.json               # NPM dependencies
│   ├── vite.config.ts            # Vite configuration
│   ├── tsconfig.json             # TypeScript configuration
│   └── tailwind.config.cjs        # Tailwind CSS configuration
│
├── .env                           # Environment variables
├── .env.example                   # Example environment file
├── .gitignore                     # Git ignore rules
├── config.json                    # Application configuration
├── requirements.txt               # (Root level - optional)
└── README.md                      # Project documentation
```

## Running the Application

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python copilot_backend.py
```

The backend will run on **http://localhost:8000**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on **http://localhost:5173**

The frontend is configured to proxy API requests to `http://127.0.0.1:8000`

## Environment Variables

Create `.env` files in both backend and frontend directories:

**backend/.env:**
```
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
JWT_SECRET=your_jwt_secret
DATABASE_URL=sqlite:///./auth.db
```

**frontend/.env.local:**
```
VITE_API_URL=http://localhost:8000
```

## Key Features

- **AI-Powered Supply Chain Chatbot** using Groq & OpenAI LLMs
- **1M Shipment Dataset** analysis in real-time
- **JWT Authentication** with SQLite backend
- **Real-time Metrics** extraction via LLM CSV analysis
- **Full-screen Chat Interface** with compact KPI dashboard
- **Responsive React UI** with Material-UI & Tailwind CSS

## API Endpoints

- `POST /chat` - Send a query to the AI chatbot
- `POST /auth/login` - Login with credentials
- `POST /auth/logout` - Logout user
- `GET /auth/verify` - Verify authentication token
- `GET /health` - Health check endpoint

## Authentication

Default credentials:
- **Email:** admin@productx.com
- **Password:** admin123

Change these in `backend/auth_db.py`
