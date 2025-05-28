from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import email_controller, optimization_controller

app = FastAPI(title="Loop Learner Backend", version="0.1.0")

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(email_controller.router)
app.include_router(optimization_controller.router)

@app.get("/")
async def root():
    return {"message": "Loop Learner Backend"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}