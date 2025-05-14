from fastapi import FastAPI
from .routers import auth_router, user_router, product_router, user_profile_router, order_router # Added order_router

app = FastAPI(
    title="Radware Vulnerable E-commerce API",
    description="An intentionally vulnerable e-commerce API designed to demonstrate business logic attacks, focusing on path and query parameters.",
    version="1.0.0"
)

app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(user_router.router, tags=["Users"]) 
app.include_router(product_router.router, tags=["Products", "Stock"])
app.include_router(user_profile_router.router) # No prefix here as it's defined in the router itself
app.include_router(order_router.router, tags=["Orders"]) # Added order_router

@app.get("/")
async def root():
    return {"message": "Hello World"}
