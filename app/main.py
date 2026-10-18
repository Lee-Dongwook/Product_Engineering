from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.exceptions import SCMException

app = FastAPI(
    title="SCM Inventory Optimization Agent Platform API",
    version="0.1.0"
)

@app.exception_handler(SCMException)
async def scm_exception_handler(request: Request, exc: SCMException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "path": request.url.path
        }
    )

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "scm-backend"}
