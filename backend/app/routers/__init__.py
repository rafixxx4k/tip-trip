from fastapi import APIRouter

api_router = APIRouter()

# Import and include routers from submodules
from app.routers import users
from app.routers import trips
from app.routers import user_trips
from app.routers import dates
from app.routers import chat
from app.routers import expenses

api_router.include_router(users.router, prefix="", tags=["users"])
api_router.include_router(trips.router, prefix="", tags=["trips"])
api_router.include_router(user_trips.router, prefix="", tags=["user-trips"])
api_router.include_router(dates.router, prefix="", tags=["dates"])
api_router.include_router(chat.router, prefix="", tags=["chat"])
api_router.include_router(expenses.router, prefix="", tags=["expenses"])
