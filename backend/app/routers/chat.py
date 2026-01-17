from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import os

from app.db.session import get_db
from app.models.user import User
from app.models.trip import Trip
from app.models.user_trip import UserTrip
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://chat:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")


def get_authenticated_user(
    x_user_hash: Optional[str] = Header(None), db: Session = Depends(get_db)
) -> User:
    """Dependency that authenticates a request using X-User-Hash header (user token)."""
    if not x_user_hash:
        raise HTTPException(status_code=401, detail="X-User-Hash header missing")
    user = db.query(User).filter(User.token == x_user_hash).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user hash")
    return user


@router.post("/trips/{trip_hash}/chat", response_model=ChatResponse)
async def send_chat_message(
    trip_hash: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    """
    Send a message to the AI travel assistant for a specific trip.
    The AI will provide recommendations and assistance based on trip context.
    """
    # Verify trip exists and user is a member
    trip = db.query(Trip).filter(Trip.hash_id == trip_hash).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    membership = (
        db.query(UserTrip)
        .filter(UserTrip.trip_id == trip.id, UserTrip.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this trip")

    # Build context for the AI
    member_count = db.query(UserTrip).filter(UserTrip.trip_id == trip.id).count()
    context = f"""You are a helpful AI travel assistant for the trip "{trip.title}".
The trip has {member_count} members."""

    if trip.date_start and trip.date_end:
        context += f"\nThe trip is planned from {trip.date_start} to {trip.date_end}."

    if trip.description:
        context += f"\nTrip description: {trip.description}"

    context += "\n\nProvide helpful, concise recommendations for destinations, activities, restaurants, packing tips, and general travel advice."

    # Call Ollama API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            ollama_payload = {
                "model": OLLAMA_MODEL,
                "prompt": f"{context}\n\nUser question: {payload.message}\n\nAssistant:",
                "stream": False,
            }

            response = await client.post(
                f"{OLLAMA_API_URL}/api/generate", json=ollama_payload
            )
            response.raise_for_status()

            data = response.json()
            ai_response = data.get("response", "").strip()

            if not ai_response:
                ai_response = (
                    "I apologize, but I couldn't generate a response. Please try again."
                )

            return ChatResponse(response=ai_response)

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503, detail=f"Failed to connect to AI service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing AI request: {str(e)}"
        )
