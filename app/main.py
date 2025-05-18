from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth_router, user_router, product_router, user_profile_router, order_router # Added order_router

app = FastAPI(
    title="Radware Vulnerable E-commerce API",
    description="An intentionally vulnerable e-commerce API designed to demonstrate business logic attacks, focusing on path and query parameters.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demonstration purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(user_router.router, prefix="/api", tags=["Users"]) 
app.include_router(product_router.router, prefix="/api", tags=["Products", "Stock"])
app.include_router(user_profile_router.router, prefix="/api") # No prefix here as it's defined in the router itself
app.include_router(order_router.router, prefix="/api", tags=["Orders"]) # Added order_router

@app.get("/")
async def root():
    return {"message": "Hello World"}
