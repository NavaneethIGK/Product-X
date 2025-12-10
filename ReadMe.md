# 📦 Product X - Supply Chain AI Copilot

Enterprise-grade AI-powered supply chain analytics platform with real-time shipment monitoring, predictive analytics, and intelligent insights.

## 🎯 Overview

Product X is a full-stack application that analyzes 1M+ shipment records to provide:
- 🤖 **AI Copilot** - Conversational analytics with structured SQL-like queries
- 📊 **Predictive Analytics** - Delay prediction and risk assessment
- 📈 **Real-time Dashboards** - Live metrics and trend analysis
- 🔍 **Intelligent Insights** - Generative recommendations for optimization

### Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite (fast build tool)
- Recharts (data visualization)
- Tailwind CSS (styling)
- React Markdown (rich text rendering)

**Backend:**
- FastAPI (Python web framework)
- Pandas (data processing)
- CORS support for cross-origin requests

**Data:**
- CSV-based dataset (1,000,000 shipment records)
- In-memory processing with Pandas

---

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- Git

### Local Development

**1. Clone Repository**
\`\`\`bash
git clone https://github.com/NavaneethIGK/Product-X.git
cd Product-X
\`\`\`

**2. Setup Backend**
\`\`\`bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn pandas python-multipart

# Run backend
python copilot_backend.py
\`\`\`

Backend runs on: \`http://localhost:8000\`

**3. Setup Frontend**
\`\`\`bash
cd product-x-dashboard

# Install dependencies
npm install

# Run development server
npm run dev
\`\`\`

Frontend runs on: \`http://localhost:5175\`

**4. Open in Browser**
\`\`\`
http://localhost:5175
\`\`\`

---

## 📋 Features

### 🤖 AI Copilot
Conversational interface for supply chain analytics:
- **Structured Queries**: "How many SKUs?", "Which routes have delays?"
- **Generative Insights**: "How can we improve?", "What are the bottlenecks?"
- **NLP → SQL Pipeline**: Converts natural language to data queries
- **Real-time Analysis**: Instant answers from 1M shipment dataset
- **Smart Aggregations**: Intelligent detection of "most" vs "least" queries ⭐ NEW

**Example Questions:**
- "How many SKUs do we have?" → Returns: 500 unique SKUs
- "Which SKU have more shipments?" → Returns: Top 10 SKUs by order count
- "What's causing delays?" → Returns: Analysis of problematic routes/SKUs
- "How can we reduce delays?" → Returns: Actionable recommendations
- **"Which destination has less shipment?"** → Returns: Ranked destinations by least shipments ⭐ NEW
- **"Show 5 sources with fewest shipments"** → Returns: Top 5 sources, ranked ⭐ NEW

### 📊 AI Predictions
Advanced analytics dashboard with:
- ✅ **KPI Cards** - Total shipments, on-time rate, delay rate
- 📉 **Trend Charts** - Weekly performance trends
- 🎯 **Risk Distribution** - Low/Medium/High risk shipments
- 💾 **Confidence Levels** - Prediction confidence breakdown
- 🌈 **Modern UI** - Gradient cards, smooth animations

### 🔄 Real-time Data Processing
- Loads 1M shipment CSV into memory
- Aggregates metrics on demand
- No database required - pure CSV + Pandas
- Sub-second response times

---

## 🏗️ Architecture

### Smart Query Engine ⭐ NEW
Intelligent, data-driven query system that automatically:
- ✅ Detects aggregation dimensions (destination, source, SKU, route, status)
- ✅ Recognizes sort direction ("least" vs "most")
- ✅ Returns properly ranked results
- ✅ Works with ANY query structure (no manual patterns needed)

**Example:** "Which destination has less shipment?"
- Old System: Returns unranked list with all destinations showing "1 shipment"
- New System: Returns ranked list from fewest to most shipments

See `SMART_QUERY_GUIDE.md` for detailed documentation.

### Request Flow

\`\`\`
User Query
    ↓
Smart Intent Detection (Keyword Analysis)
    ↓
Aggregation Type & Sort Direction Detected
    ↓
SQL-like Execution on CSV
    ↓
Data Aggregation + Ranking
    ↓
Formatted Response
    ↓
Optional: LLM Enrichment
    ↓
Response to User
\`\`\`

### Query Types (9 Types + Smart Aggregations)

| Query Type | Example | Response |
|-----------|---------|----------|
| \`sku_count\` | "How many SKUs?" | Total unique SKUs |
| \`orders_per_sku\` | "Which SKU have more orders?" | Top SKUs by count |
| \`top_routes\` | "Show top routes" | Routes by shipment volume |
| \`delayed_shipments\` | "Show delays" | List of delayed orders |
| \`sku_delay_analysis\` | "Problem SKUs" | SKUs by delay rate |
| \`route_delay_analysis\` | "Route performance" | Routes by delay rate |
| \`filtered_shipments\` | "Filter by SKU-123" | Shipments matching filter |
| \`summary_stats\` | "Overview" | All key metrics |
| \`generative_insights\` | "How to improve?" | Actionable recommendations |

---

## 📁 Project Structure

\`\`\`
Product-X/
├── copilot_backend.py          # FastAPI backend
├── query_engine.py             # SQL-like query handlers
├── intent_detector.py          # NLP intent recognition
├── smart_query_engine.py       # ⭐ NEW: Intelligent data-driven queries
├── data_enrichment.py          # Data transformation layer
├── ai_providers_groq.py        # Groq AI integration
├── ai_providers_openai.py      # OpenAI integration
├── shipment_data_1M.csv        # 1M shipment records
├── requirements.txt            # Python dependencies
│
├── SMART_QUERY_GUIDE.md        # ⭐ NEW: Complete smart query documentation
├── SOLUTION_SUMMARY.md         # ⭐ NEW: Implementation details
├── CHATBOT_FIXES.md            # Bug fixes and improvements
│
└── product-x-dashboard/        # React frontend
    ├── src/
    │   ├── components/
    │   │   ├── AICopilot.tsx           # Chat interface
    │   │   ├── AICopilotChat.tsx       # Message display
    │   │   ├── Sidebar.tsx             # Navigation
    │   │   └── PredictionsAnalytics.tsx # Analytics dashboard
    │   ├── App.tsx
    │   ├── index.css
    │   └── main.tsx
    ├── public/
    │   └── models.json          # LLM model definitions
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
\`\`\`

---

## 🔌 API Endpoints

### Smart Chat Endpoint ⭐ NEW
\`\`\`http
POST /chat/smart
Content-Type: application/json

{
  "query": "Which destination has less shipment?"
}
\`\`\`

**Response:**
\`\`\`json
{
  "response": "📊 Destinations with fewest shipments (top 10):\n  1. UK-LON (1 shipment, 50 units)\n  2. DE-FRA (2 shipments, 100 units)\n  ...",
  "session_id": "uuid",
  "smart_query": true,
  "intent": {
    "aggregation": "destination",
    "sort_order": "ascending",
    "limit": 10,
    "confidence": 0.95
  },
  "structured_data": {
    "summary": "Destinations with fewest shipments (top 10)",
    "data": [
      {"destination": "UK-LON", "shipment_count": 1, "total_quantity": 50},
      {"destination": "DE-FRA", "shipment_count": 2, "total_quantity": 100}
    ],
    "total_unique": 8
  }
}
\`\`\`

**Supported Queries:**
- "which destination has less shipment" → Ranked by fewest shipments
- "top sources by shipment count" → Ranked by most shipments
- "show 5 SKUs with fewest orders" → Top 5 SKUs with least volume
- "slowest routes" → Routes ranked by least shipments
- "busiest corridors" → Routes ranked by most shipments

---

### Chat Endpoint (Original)
\`\`\`http
POST /chat
Content-Type: application/json

{
  "query": "Which SKU have more shipments?",
  "messages": []
}
\`\`\`

**Response:**
\`\`\`json
{
  "response": "Markdown formatted answer",
  "intent": "orders_per_sku",
  "confidence": 0.95,
  "structured_data": {
    "query_type": "orders_per_sku",
    "records": [
      {"SKU": "SKU-0481", "order_count": 2156},
      {"SKU": "SKU-0076", "order_count": 2098}
    ],
    "total_records": 500
  }
}
\`\`\`

---

## 📊 CSV Data Format

Expected columns in \`shipment_data.csv\`:

\`\`\`
order_id,SKU,ROUTE,STATUS,expected_arrival,arrived_at,delay_days
1,SKU-0481,NYC→LA,ARRIVED,2024-01-13,2024-01-15,2
2,SKU-0076,CHI→MIA,IN_TRANSIT,2024-01-20,,0
3,SKU-0029,NYC→LA,DELAYED,2024-01-10,,5
\`\`\`

**Required Columns:**
- \`order_id\` - Unique identifier
- \`SKU\` - Product SKU code
- \`ROUTE\` - Shipping route
- \`STATUS\` - ARRIVED, IN_TRANSIT, or DELAYED
- \`expected_arrival\` - Expected delivery date
- \`arrived_at\` - Actual delivery date
- \`delay_days\` - Days delayed (calculated)

---

## 🐳 Docker Deployment

### Build Docker Image
\`\`\`bash
docker build -t product-x .
\`\`\`

### Run Container
\`\`\`bash
docker run -p 8000:8000 -p 5175:5175 product-x
\`\`\`

---

## 🖥️ Linux VM Deployment

### Prerequisites
\`\`\`bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip nodejs npm git nginx
\`\`\`

### Deploy Backend
\`\`\`bash
cd /home/user/Product-X
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pandas python-multipart
nohup python copilot_backend.py > backend.log 2>&1 &
\`\`\`

### Deploy Frontend
\`\`\`bash
cd /home/user/Product-X/product-x-dashboard
npm install
npm run build
nohup npm run preview -- --host 0.0.0.0 > frontend.log 2>&1 &
\`\`\`

### Setup Nginx Reverse Proxy
\`\`\`bash
sudo nano /etc/nginx/sites-available/product-x
# Add configuration
sudo systemctl restart nginx
\`\`\`

### Access Application
\`\`\`
http://your_vm_ip
\`\`\`

---

## 🔧 Configuration

### Backend Config (\`copilot_backend.py\`)
\`\`\`python
# Port
PORT = 8000

# CORS allowed origins
ALLOWED_ORIGINS = ["http://localhost:5175", "http://your_domain.com"]

# CSV path
CSV_PATH = "./shipment_data.csv"
\`\`\`

### Frontend Config (\`vite.config.ts\`)
\`\`\`typescript
// API endpoint
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
\`\`\`

---

## 📈 Performance

**Dataset**: 1,000,000 shipment records

**Response Times:**
- SKU count query: ~50ms
- Orders per SKU: ~200ms
- Generative insights: ~500ms (includes LLM call)

**Memory Usage:**
- CSV loaded: ~150MB
- Peak during aggregation: ~500MB

---

## 🐛 Troubleshooting

### Backend Won't Start
\`\`\`bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process
kill -9 <PID>

# Try different port
python copilot_backend.py --port 8001
\`\`\`

### Frontend Won't Build
\`\`\`bash
# Clear cache
rm -rf node_modules package-lock.json
npm install
npm run build
\`\`\`

### CSV Not Found
\`\`\`bash
# Place CSV in correct location
cp shipment_data.csv ./shipment_data.csv
\`\`\`

### CORS Errors
\`\`\`bash
# Add your domain to ALLOWED_ORIGINS in copilot_backend.py
ALLOWED_ORIGINS = ["http://localhost:5175", "https://your_domain.com"]
\`\`\`

---

## 📝 Query Examples

### Structured Analytics
\`\`\`
User: "How many SKUs?"
Copilot: "There are 500 unique SKUs in your supply chain."

User: "Which routes have the most delays?"
Copilot: "Top 5 routes by delay rate:
- NYC→LA: 65.2% delay rate
- CHI→MIA: 62.1% delay rate
..."
\`\`\`

### Generative Insights
\`\`\`
User: "How can we improve delivery performance?"
Copilot: "Based on analysis of 1M shipments:

🔴 HIGH PRIORITY:
- SKU-0481 has 65.7% delay rate - investigate packaging
- Route NYC→LA consistently delayed - consider alternative carriers

📊 RECOMMENDATIONS:
1. Focus on top 3 problematic SKUs
2. Optimize high-delay routes
3. Implement real-time tracking alerts
..."
\`\`\`

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (\`git checkout -b feature/improvement\`)
3. Commit changes (\`git commit -m 'Add improvement'\`)
4. Push to branch (\`git push origin feature/improvement\`)
5. Open Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 📞 Support

For issues and questions:
- GitHub Issues: [Product-X Issues](https://github.com/NavaneethIGK/Product-X/issues)
- Email: your-email@example.com

---

## 🎯 Roadmap

- [ ] PostgreSQL integration for larger datasets
- [ ] Machine learning delay prediction model
- [ ] Mobile app support
- [ ] Real-time WebSocket updates
- [ ] Custom report generation
- [ ] Multi-tenant support
- [ ] Advanced forecasting

---

**Made with ❤️ for supply chain excellence**