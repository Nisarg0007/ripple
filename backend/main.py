from fastapi import FastAPI

app = FastAPI(
    title="Ripple API",
    description="Impact analysis engine for code changes",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"service": "Ripple API", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
