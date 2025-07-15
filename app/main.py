# app/main.py
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os
import yaml
from .routers import (
    auth_router,
    user_router,
    product_router,
    user_profile_router,
    order_router,
    coupon_router,
)
import logging
import json
import time  # For response time logging
from pydantic import BaseModel

# Provide compatibility with Pydantic v1 by aliasing model_validate and model_dump
if not hasattr(BaseModel, "model_validate"):

    def _model_validate(cls, obj):
        if isinstance(obj, cls):
            return obj
        if hasattr(obj, "dict"):
            obj = obj.dict()
        elif hasattr(obj, "__dict__"):
            obj = obj.__dict__
        return cls.parse_obj(obj)

    BaseModel.model_validate = classmethod(_model_validate)

if not hasattr(BaseModel, "model_dump"):

    def _model_dump(self, *args, **kwargs):
        return self.dict(*args, **kwargs)

    BaseModel.model_dump = _model_dump

# --- REMOVE CustomAccessJsonFormatter and formatter_debug_logger from here ---
# They are no longer needed as we're using a middleware to capture data.

# Define a dedicated logger for our custom access logs
# This logger will be configured in log_conf.json
custom_access_logger = logging.getLogger("app.access")


# --- Custom Middleware to Capture Request Details ---
class CustomAccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract headers and client IP directly from the Request object
        # Request.headers provides a MultiDict of headers
        headers = request.headers

        authorization_header = headers.get(
            "authorization"
        )  # FastAPI/Starlette headers are already lowercase
        x_rdwr_ip = headers.get("x-rdwr-ip")
        x_forwarded_for = headers.get("x-forwarded-for")

        # Determine client IP with priority: X-Rdwr-ip > X-Forwarded-For > Request.client.host
        client_ip = None
        if x_rdwr_ip:
            client_ip = x_rdwr_ip
        elif x_forwarded_for:
            # X-Forwarded-For can be a comma-separated list, take the first one
            client_ip = x_forwarded_for.split(",")[0].strip()
        elif request.client and request.client.host:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        # Process the request and get the response
        response = await call_next(request)

        process_time = time.time() - start_time

        # Prepare the log data as a dictionary
        log_data = {
            "request_id": str(time.time()),  # Simple request ID for correlation
            "client_ip": client_ip,
            "request_method": request.method,
            "request_path": request.url.path,
            "request_query_string": str(request.url.query),
            "response_status": response.status_code,
            "response_time_ms": round(process_time * 1000, 2),
            "authorization": authorization_header,  # Will be None if header not present
            # Add any other headers you want to log explicitly here
            # "user_agent": headers.get("user-agent"),
        }

        # Log the structured data using our dedicated logger
        # We pass the dictionary directly as 'extra' or as the message itself
        # For python-json-logger, passing it as the message is often cleaner
        custom_access_logger.info(log_data)

        return response


# Your FastAPI app definition
app = FastAPI(
    title="Radware Vulnerable E-commerce API",
    description="An intentionally vulnerable e-commerce API designed to demonstrate business logic attacks, focusing on path and query parameters.",
    version="1.0.0",
)

# Use the pre-generated OpenAPI specification from openapi.yaml
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def custom_openapi() -> dict:
    """Load the OpenAPI schema from the repository's openapi.yaml file."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_path = os.path.join(BASE_DIR, "openapi.yaml")
    with open(openapi_path, "r") as f:
        app.openapi_schema = yaml.safe_load(f)
    return app.openapi_schema


app.openapi = custom_openapi

# Add the custom middleware to your FastAPI app
if os.getenv("ENABLE_ACCESS_LOG", "false").lower() == "true":
    app.add_middleware(CustomAccessLogMiddleware)

# Add CORS middleware (keep this as it's part of your app's functionality)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(user_router.router, prefix="/api", tags=["Users"])
app.include_router(product_router.router, prefix="/api", tags=["Products", "Stock"])
app.include_router(user_profile_router.router, prefix="/api")
app.include_router(order_router.router, prefix="/api", tags=["Orders"])
app.include_router(
    coupon_router.router,
    prefix="/api",
    tags=["Coupons", "Admin"],
)

from . import sync


@app.on_event("startup")
async def start_sync_service() -> None:
    """Start background DB sync if configured."""
    sync.start_background_sync()


@app.get("/")
async def root():
    return {"message": "Hello World"}
