from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.product_routes import router as product_router
from routes.price_routes import router as price_router
from routes.competitor_routes import router as competitor_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(product_router, prefix="/api")
app.include_router(price_router, prefix="/api")
app.include_router(competitor_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to PriceSpy Backend"}