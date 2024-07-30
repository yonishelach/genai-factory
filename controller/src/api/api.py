from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.src.api.endpoints import (
    chat_sessions,
    datasets,
    data_sources,
    documents,
    models,
    projects,
    prompt_templates,
    tables,
    users,
    workflows,
)
app = FastAPI()

# Add CORS middleware, remove in production
origins = ["*"]  # React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with a prefix
api_router = APIRouter(prefix="/api")

# Include the routers for the different endpoints
api_router.include_router(
    tables.router,
    tags=["tables"],
)
api_router.include_router(
    projects.router,
    tags=["projects"],
)
api_router.include_router(
    data_sources.router,
    tags=["data_sources"],
)
api_router.include_router(
    datasets.router,
    tags=["datasets"],
)
api_router.include_router(
    models.router,
    tags=["models"],
)
api_router.include_router(
    prompt_templates.router,
    tags=["prompt_templates"],
)
api_router.include_router(
    documents.router,
    tags=["documents"],
)
api_router.include_router(
    workflows.router,
    tags=["workflows"],
)
api_router.include_router(
    users.router,
    tags=["users"],
)
api_router.include_router(
    chat_sessions.router,
    tags=["chat_sessions"],
)

# Include the router in the main app
app.include_router(api_router)

# TODO: Finished here yesterday, only added the new endpoints,
#  need also to add the old endpoints and check if everything works as before.
