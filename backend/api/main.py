import sys
import asyncio
import platform

if platform.system() == "Windows":
    # Force Uvicorn loop factory to use Selector event loop instead of Proactor (required by psycopg)
    try:
        import uvicorn.loops.asyncio as uvicorn_asyncio
        uvicorn_asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    except ImportError:
        pass
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from backend.api.routes import chat, upload
from backend import config as app_config
from backend.db.connection import init_pool, close_pool
from backend.api.routes.upload import cleanup_old_uploads
from backend.db.migrations import run_migrations
from backend.api.routes import chat, upload, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print("[startup] Cleaning up old uploads...")
    await cleanup_old_uploads()
    # Init DB connection pool
    print("[startup] Connecting to Neon...")
    await init_pool()
    print("[startup] DB pool ready.")

    print("[startup] Running migrations...")
    await run_migrations()
    print("[startup] Migrations complete.")
    
    # Warm up embeddings
    print("[startup] Loading embedding model...")
    app_config.get_embeddings()
    print("[startup] Embeddings ready.")

    # Initialize Postgres checkpointer and compile graph
    print("[startup] Initializing checkpointer...")

    async with AsyncConnectionPool(
        conninfo=app_config.NEON_DATABASE_URL,
        min_size=0,
        max_size=5,
        max_idle=30,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
            "prepare_threshold": 0
        }
    ) as pool:
        checkpointer = AsyncPostgresSaver(conn=pool)
        await checkpointer.setup()  # creates langgraph checkpoint tables if not exist

        from backend.graph import graph_builder

        compiled = graph_builder.compile(
            checkpointer=checkpointer,
            interrupt_before=["clarification"]
        )

        app.state.graph = compiled
        print("[startup] Graph compiled and ready.")

        yield

    # Cleanup
    await close_pool()
    print("[shutdown] Cleaning up...")


app = FastAPI(
    title="Multimodal Agent API",
    description="LangGraph-powered multimodal RAG agent",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router,   prefix="/api/v1", tags=["auth"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(chat.router,   prefix="/api/v1", tags=["chat"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "0.1.0"}