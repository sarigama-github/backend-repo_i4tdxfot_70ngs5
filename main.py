import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

app = FastAPI(title="AI Automation Agency API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Health
# -----------------------------
@app.get("/")
def read_root():
    return {"message": "AI Automation Agency Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


# -----------------------------
# Database diagnostic
# -----------------------------
@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# -----------------------------
# Data models for simple content endpoints
# -----------------------------
class TeamMember(BaseModel):
    name: str
    role: str
    bio: str
    avatar: Optional[str] = None
    socials: Dict[str, str] = {}

class CaseStudy(BaseModel):
    client: str
    industry: str
    challenge: str
    solution: str
    impact_metrics: Dict[str, Any]

class QuizInput(BaseModel):
    industry: str = Field(..., description="e.g., ecommerce, finance, saas, healthcare")
    company_size: str = Field(..., description="e.g., startup, smb, midmarket, enterprise")
    primary_goal: str = Field(..., description="e.g., lead-gen, support, operations, analytics")

class Recommendation(BaseModel):
    title: str
    description: str
    icon: str
    priority: int

class ChatbotMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


# -----------------------------
# Static data (for demo purposes)
# -----------------------------
TECHNOLOGIES = [
    {"name": "Machine Learning", "icon": "Brain"},
    {"name": "NLP", "icon": "MessageSquare"},
    {"name": "RPA", "icon": "Workflow"},
    {"name": "Computer Vision", "icon": "Scan"},
    {"name": "Data Engineering", "icon": "Database"},
    {"name": "MLOps", "icon": "Settings"},
]

TEAM: List[TeamMember] = [
    TeamMember(name="Ava van Rijn", role="Head of AI Strategy", bio="Ontwerpt schaalbare AI-roadmaps voor impact.", avatar="/avatars/ava.png", socials={"linkedin": "#"}),
    TeamMember(name="Milan de Groot", role="Lead ML Engineer", bio="Production-grade ML met focus op betrouwbaarheid.", avatar="/avatars/milan.png", socials={"linkedin": "#"}),
    TeamMember(name="Noa Janssen", role="Automation Architect", bio="RPA en integraties die processen laten stromen.", avatar="/avatars/noa.png", socials={"linkedin": "#"}),
]

CASE_STUDIES: List[CaseStudy] = [
    CaseStudy(
        client="Nova Retail",
        industry="E-commerce",
        challenge="Hoge workload bij customer support en trage responstijden.",
        solution="NLP-gedreven virtuele agent en auto-triage met RPA.",
        impact_metrics={"CSAT": "+18%", "First Response": "-62%", "Hours Saved/mo": 450},
    ),
    CaseStudy(
        client="FinOptima",
        industry="Financieel",
        challenge="Handmatige rapportage en compliance processen.",
        solution="Automatische document parsing en ML-anomalie detectie.",
        impact_metrics={"Reporting Time": "-70%", "Accuracy": "+2.3%"},
    ),
]

SERVICE_LIBRARY: List[Recommendation] = [
    Recommendation(title="AI-driven Customer Service", description="Virtuele agents, intent-herkenning en self-service flows.", icon="Headset", priority=1),
    Recommendation(title="Marketing Automation", description="Personalisatie, lead scoring en lifecycle journeys.", icon="Sparkles", priority=2),
    Recommendation(title="ML Applications", description="Voorspellende modellen, aanbevelers en detectie.", icon="BrainCircuit", priority=2),
    Recommendation(title="RPA & Integrations", description="Robotica voor repetitieve taken en systeemkoppelingen.", icon="Workflow", priority=3),
    Recommendation(title="Analytics & Dashboards", description="Realtime KPI’s met datamodellering en visualisatie.", icon="BarChart3", priority=3),
]


# -----------------------------
# Public content endpoints
# -----------------------------
@app.get("/api/technologies")
def get_technologies():
    return TECHNOLOGIES

@app.get("/api/team", response_model=List[TeamMember])
def get_team():
    return TEAM

@app.get("/api/case-studies", response_model=List[CaseStudy])
def get_case_studies():
    return CASE_STUDIES


# -----------------------------
# Quiz-based recommendation
# -----------------------------
@app.post("/api/recommend", response_model=List[Recommendation])
def recommend(payload: QuizInput):
    industry = payload.industry.lower()
    size = payload.company_size.lower()
    goal = payload.primary_goal.lower()

    results: List[Recommendation] = []

    if goal in ["support", "customer support", "cs"]:
        results.append(SERVICE_LIBRARY[0])
    if goal in ["lead-gen", "marketing", "growth", "revenue"]:
        results.append(SERVICE_LIBRARY[1])
    if goal in ["analytics", "insights", "reporting"]:
        results.append(SERVICE_LIBRARY[4])
    if goal in ["operations", "efficiency", "process"]:
        results.append(SERVICE_LIBRARY[3])

    if industry in ["ecommerce", "e-commerce"]:
        results.append(SERVICE_LIBRARY[2])
    if industry in ["finance", "fintech", "financial"]:
        results.append(SERVICE_LIBRARY[2])

    if size in ["enterprise", "midmarket"]:
        results.append(SERVICE_LIBRARY[3])

    # Fallback to a balanced trio if empty
    if not results:
        results = [SERVICE_LIBRARY[2], SERVICE_LIBRARY[0], SERVICE_LIBRARY[4]]

    # Unique by title, sorted by priority
    dedup: Dict[str, Recommendation] = {rec.title: rec for rec in results}
    return sorted(dedup.values(), key=lambda r: r.priority)


# -----------------------------
# Simple rule-based chatbot
# -----------------------------
@app.post("/api/chatbot")
def chatbot(msg: ChatbotMessage):
    text = (msg.message or "").lower()
    def reply(content: str, intent: str = "general", suggestions: Optional[List[str]] = None):
        return {"reply": content, "intent": intent, "suggestions": suggestions or []}

    if any(k in text for k in ["prijs", "kosten", "tarief", "offerte", "pricing", "price"]):
        return reply(
            "Onze trajecten starten doorgaans vanaf €8.000 voor een pilot. Voor langdurige implementaties werken we met vaste sprints of een retainer. Zal ik een korte intake van 15 min inplannen?",
            intent="pricing",
            suggestions=["Plan een intake", "Stuur prijslijst", "Meer over pakketten"],
        )
    if any(k in text for k in ["implement", "implementatie", "hoe werkt", "proces", "stappen"]):
        return reply(
            "We starten met een AI Discovery (1-2 weken), vervolgens een pilot (4-6 weken) en daarna schaalvergroting. Alles is meetbaar met KPI’s en dashboards.",
            intent="process",
            suggestions=["Start Discovery", "Bekijk voorbeelden", "Meetbare KPI’s"],
        )
    if any(k in text for k in ["support", "klantenservice", "customer service", "helpdesk"]):
        return reply(
            "Voor support automatisering combineren we NLP met workflow-automatisering (RPA). Gemiddeld reduceren we responstijden met 50-70%.",
            intent="service-support",
            suggestions=["Plan demo virtuele agent", "Zie case retail", "Integraties"],
        )
    if any(k in text for k in ["marketing", "lead", "campagne", "growth"]):
        return reply(
            "We bouwen scoring-modellen, personalisatie en journey-automatisering. Dit leidt vaak tot +10-25% conversie uplift.",
            intent="service-marketing",
            suggestions=["Plan marketing audit", "Voorbeeldflows", "CDP integratie"],
        )
    if any(k in text for k in ["ml", "machine learning", "model", "ai"]):
        return reply(
            "We ontwikkelen productierijpe ML met MLOps best practices: monitoring, retraining en CI/CD voor modellen.",
            intent="service-ml",
            suggestions=["Architectuur voorbeelden", "Security & compliance", "Roadmap sessie"],
        )
    # Default
    return reply(
        "Hi! Ik ben je AI-assistent. Stel me een vraag over onze diensten, implementatie of prijzen, of vraag om een intake.",
        intent="general",
        suggestions=["Wat kost een pilot?", "Hoe ziet het proces eruit?", "Welke cases hebben jullie?"],
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
