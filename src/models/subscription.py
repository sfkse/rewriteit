from enum import Enum
from pydantic import BaseModel, Field

class SubscriptionPlan(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class SubscriptionRequest(BaseModel):
    plan: SubscriptionPlan = Field(..., description="The subscription plan to subscribe to")

class SubscriptionResponse(BaseModel):
    url: str = Field(..., description="The Stripe Checkout URL")

class PortalSessionRequest(BaseModel):
    session_id: str = Field(..., description="The Stripe Checkout session ID")

class PortalSessionResponse(BaseModel):
    url: str = Field(..., description="The Stripe Customer Portal URL")

class SubscriptionPrice(BaseModel):
    monthly: str = "price_monthly"  # Will be replaced with actual Stripe price ID
    yearly: str = "price_yearly"    # Will be replaced with actual Stripe price ID

SUBSCRIPTION_PRICES = {
    SubscriptionPlan.MONTHLY: {
        "amount": 999,  # $9.99
        "currency": "usd",
        "interval": "month",
        "product_name": "RewordIt Monthly Plan"
    },
    SubscriptionPlan.YEARLY: {
        "amount": 8999,  # $89.99
        "currency": "usd",
        "interval": "year",
        "product_name": "RewordIt Yearly Plan"
    }
} 