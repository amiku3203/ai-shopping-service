from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.search import router as search_router
from routes.agent import router as agent_router
from config import settings

app = FastAPI(
    title="AI Shopping Service",
    description="AI-powered search microservice",
    version="1.0.0"
)

# -------------------------
# CORS (important for MERN)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://infinite-mart-ecom.vercel.app",
        "*" # Keep wildcard for dev flexibility if needed, or remove for strict security
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Routes
# -------------------------
app.include_router(search_router)
app.include_router(agent_router)


# -------------------------
# Health Check
# -------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
    }
