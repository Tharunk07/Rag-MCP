from fastapi import FastAPI
from config import API_PREFIX, API_VERSION, allow_credentials, allow_headers, allow_methods, allow_origins
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastmcp import FastMCP, settings
import logging
from fastapi.middleware import Middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os


settings.stateless_http = True

# Initialize FastMCP
mcp = FastMCP(name="MultiModel_RAG")

# Create the MCP app with the root path
mcp_app = mcp.http_app(path="/")

# Initialize FastAPI with FastMCP lifespan
app = FastAPI(
    title="MultiModel RAG",
    summary="MultiModel RAG APIs",
    version=API_VERSION,
    redoc_url=f"{API_PREFIX}/redoc",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
    lifespan=mcp_app.lifespan,
)

# Mount the FastMCP app
app.mount("/rag/rag-mcp", mcp_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)

# Ensure the logs directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - [%(name)s] [%(process)s] - [%(module)s.%(funcName)s, line %(lineno)s] - %(message)s",
    handlers=[
        logging.handlers.TimedRotatingFileHandler(
            "logs/ragmcp-backend.log",
            when="midnight",
            interval=1,
            backupCount=7,
        ),
        logging.StreamHandler(),
    ],
    datefmt="%Y-%m-%d %H:%M:%S %Z",
)

# Enable detailed logging for debugging
logging.getLogger("fastmcp").setLevel(logging.DEBUG)
logging.getLogger("mcp").setLevel(logging.DEBUG)

# Middleware
middleware = [
    Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
]

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "detail": exc.errors()},
    )

# Import routes after app initialization
from app import routes

logging.info("FastAPI application initialized successfully")
logging.info(f"MCP server mounted at: /rag/rag-mcp")