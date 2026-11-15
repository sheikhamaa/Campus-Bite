import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import ai_router, auth_router, order_router, restaurant_router
from .tasks import check_stale_orders_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("campusbite")

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(check_stale_orders_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="CampusBite API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f} ms)")
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


app.include_router(auth_router.router)
app.include_router(restaurant_router.router)
app.include_router(order_router.router)
app.include_router(ai_router.router)


@app.get("/")
def health_check():
    return {"status": "CampusBite backend running"}
