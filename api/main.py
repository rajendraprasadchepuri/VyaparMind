
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
# Import routers
from .routers import products, transactions, settings, customers
from . import database as db
from .cache import cache

app = FastAPI(
    title="VyaparMind API",
    description="High-performance backend for VyaparMind",
    version="1.0.3"
)

@app.on_event("startup")
async def startup_event():
    await cache.initialize()
    # Pre-warm connection
    await db.get_db_connection()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(products.router)
app.include_router(transactions.router)
app.include_router(settings.router)
app.include_router(customers.router)

@app.get("/")
async def root():
    return {"message": "VyaparMind API is running", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
