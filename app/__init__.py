from fastapi import FastAPI
from config import API_PREFIX, API_VERSION, allow_credentials, allow_headers, allow_methods, allow_origins
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.requests import Request
from fastmcp import FastMCP
import logging
from fastapi.middleware import Middleware
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os

mcp = FastMCP(
    name = "MultiModel_RAG",
)
mcp_app = mcp.http_app(path='/')

app = FastAPI(
    title="MultiModel RAG",
    summary="MultiModel RAG Apis",
    version=API_VERSION,
    redoc_url=f"{API_PREFIX}/redoc",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
    lifespan=mcp_app.lifespan, 
)

app.mount("/rag/rag-mcp", mcp_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - [%(name)s] [%(process)s] - [%(module)s.%(funcName)s, line %(lineno)s] - %(message)s",
    handlers=[
        logging.handlers.TimedRotatingFileHandler(
            "logs/ragmcp-backend.log",
            when="midnight",  # Corrected: 'when' should be a string
            interval=1,       # Interval remains as an integer
            backupCount=7     # Number of backup files to keep
        ),
        logging.StreamHandler(),
    ],
    datefmt="%Y-%m-%d %H:%M:%S %Z",
)

# Starlette logging middleware
middleware = [
    Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
]

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "detail": exc.errors()},
    )


from app import routes