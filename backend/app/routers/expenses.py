from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from collections import defaultdict

from app.db.session import get_db
from app.models.trip import Trip
from app.models.user_trip import UserTrip
from app.models.expense import Expense, ExpenseShare
from app.schemas.expenses import (
    ExpenseCreate,
    ExpenseRead,
    DebtorRead,
    SettlementsResponse,
    SettlementRead,
)
from app.routers.trips import get_authenticated_user
from app.models.user import User

router = APIRouter()


@router.post("/trips/{trip_hash}/expenses", response_model=ExpenseRead)
def create_expense(
    trip_hash: str,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    """Create a new expense for a trip.

    The payer is the authenticated user. Debtors are specified in the payload.
    """
    # Find trip by hash_id
    trip = db.query(Trip).filter(Trip.hash_id == trip_hash).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Verify user is a member of this trip
    membership = (
        db.query(UserTrip)
        .filter(UserTrip.trip_id == trip.id, UserTrip.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this trip")

    # Create expense
    expense = Expense(
        trip_id=trip.id,
        payer_user_id=current_user.id,
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
    )
    db.add(expense)
    db.flush()

    # Create expense shares for each debtor
    for debtor in payload.debtors:
        # Convert userId string to integer
        try:
            user_id = int(debtor.userId)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid userId: {debtor.userId}"
            )

        # Verify debtor is a member of the trip
        debtor_membership = (
            db.query(UserTrip)
            .filter(UserTrip.trip_id == trip.id, UserTrip.user_id == user_id)
            .first()
        )
        if not debtor_membership:
            raise HTTPException(
                status_code=400, detail=f"User {user_id} is not a member of this trip"
            )

        share = ExpenseShare(
            expense_id=expense.id,
            user_id=user_id,
            share_type=debtor.shareType,
            value=debtor.value,
        )
        db.add(share)

    db.commit()
    db.refresh(expense)

    # Load shares to return in response
    shares = db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense.id).all()

    return ExpenseRead(
        id=str(expense.id),
        tripId=trip.hash_id,
        payerId=str(expense.payer_user_id),
        amount=expense.amount,
        currency=expense.currency,
        description=expense.description,
        debtors=[
            DebtorRead(
                userId=str(share.user_id), shareType=share.share_type, value=share.value
            )
            for share in shares
        ],
        createdAt=expense.created_at,
    )


@router.get("/trips/{trip_hash}/expenses", response_model=List[ExpenseRead])
def get_expenses(
    trip_hash: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    """Get all expenses for a trip."""
    # Find trip by hash_id
    trip = db.query(Trip).filter(Trip.hash_id == trip_hash).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Verify user is a member of this trip
    membership = (
        db.query(UserTrip)
        .filter(UserTrip.trip_id == trip.id, UserTrip.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this trip")

    # Get all expenses for this trip
    expenses = (
        db.query(Expense)
        .filter(Expense.trip_id == trip.id)
        .order_by(Expense.created_at.desc())
        .all()
    )

    result = []
    for expense in expenses:
        shares = (
            db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense.id).all()
        )
        result.append(
            ExpenseRead(
                id=str(expense.id),
                tripId=trip.hash_id,
                payerId=str(expense.payer_user_id),
                amount=expense.amount,
                currency=expense.currency,
                description=expense.description,
                debtors=[
                    DebtorRead(
                        userId=str(share.user_id),
                        shareType=share.share_type,
                        value=share.value,
                    )
                    for share in shares
                ],
                createdAt=expense.created_at,
            )
        )

    return result


@router.get("/trips/{trip_hash}/settlements", response_model=SettlementsResponse)
def get_settlements(
    trip_hash: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    """Calculate settlements for a trip.

    This calculates who owes whom based on all expenses in the trip.
    Uses a greedy algorithm to minimize number of transactions.
    """
    # Find trip by hash_id
    trip = db.query(Trip).filter(Trip.hash_id == trip_hash).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Verify user is a member of this trip
    membership = (
        db.query(UserTrip)
        .filter(UserTrip.trip_id == trip.id, UserTrip.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this trip")

    # Get all expenses for this trip
    expenses = db.query(Expense).filter(Expense.trip_id == trip.id).all()

    if not expenses:
        return SettlementsResponse(balances=[])

    # Assume all expenses are in the same currency (use the first expense's currency)
    currency = expenses[0].currency

    # Calculate net balance for each user
    # Positive balance = they should receive money
    # Negative balance = they owe money
    balances = defaultdict(float)

    for expense in expenses:
        # Payer paid the full amount
        balances[expense.payer_user_id] += expense.amount

        # Each debtor owes their share
        shares = (
            db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense.id).all()
        )
        for share in shares:
            balances[share.user_id] -= share.value

    # Separate creditors (positive balance) and debtors (negative balance)
    creditors = [
        (user_id, amount) for user_id, amount in balances.items() if amount > 0.01
    ]
    debtors = [
        (user_id, -amount) for user_id, amount in balances.items() if amount < -0.01
    ]

    # Sort by amount (largest first) for greedy algorithm
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    # Calculate settlements using greedy algorithm
    settlements = []
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        creditor_id, credit_amount = creditors[i]
        debtor_id, debt_amount = debtors[j]

        # Settle the minimum of what's owed and what's due
        settle_amount = min(credit_amount, debt_amount)

        settlements.append(
            SettlementRead(
                fromUser=str(debtor_id),
                toUser=str(creditor_id),
                amount=round(settle_amount, 2),
                currency=currency,
            )
        )

        # Update remaining amounts
        creditors[i] = (creditor_id, credit_amount - settle_amount)
        debtors[j] = (debtor_id, debt_amount - settle_amount)

        # Move to next creditor or debtor if fully settled
        if creditors[i][1] < 0.01:
            i += 1
        if debtors[j][1] < 0.01:
            j += 1

    return SettlementsResponse(balances=settlements)
