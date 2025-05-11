#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
from fastapi import APIRouter, HTTPException, Request
import stripe
from src.config import settings
import logging
from src.models.subscription import (
    SUBSCRIPTION_PRICES,
    SubscriptionRequest,
    SubscriptionResponse,
    PortalSessionRequest,
    PortalSessionResponse
)


router = APIRouter(prefix="/subscription", tags=["subscription"])

# Initialize Stripe with the API key from config
stripe.api_key = settings.stripe_secret_key

""" @app.route('/', methods=['GET'])
def get_index():
    return current_app.send_static_file('index.html') """
logger = logging.getLogger(__name__)

@router.post("/create-checkout-session", response_model=SubscriptionResponse)
async def create_checkout_session(request: SubscriptionRequest):
    try:
        plan = request.plan
        price_details = SUBSCRIPTION_PRICES[plan]
        
        # Create or get product
        product = stripe.Product.create(
            name=price_details["product_name"],
            description=f"RewordIt {plan.capitalize()} Subscription"
        )

        # Create price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=price_details["amount"],
            currency=price_details["currency"],
            recurring={
                "interval": price_details["interval"]
            }
        )

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price.id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f"{settings.client_base_url}/checkout?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.client_base_url}/checkout?canceled=true",
            metadata={
                "plan": plan
            }
        )
        return SubscriptionResponse(url=checkout_session.url)
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")

@router.post("/create-portal-session", response_model=PortalSessionResponse)
async def customer_portal(request: PortalSessionRequest):
    try:
        checkout_session = stripe.checkout.Session.retrieve(request.session_id)
        
        portal_session = stripe.billing_portal.Session.create(
            customer=checkout_session.customer,
            return_url=settings.client_base_url,
        )
        return PortalSessionResponse(url=portal_session.url)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")

@router.post("/webhook")
async def webhook_received(request: Request):
    try:
        stripe_webhook_secret = settings.stripe_webhook_secret
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        print(f"Signature: {sig_header}")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, stripe_webhook_secret
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error('⚠️  Webhook signature verification failed.' + str(e))
            raise HTTPException(status_code=400, detail="Invalid signature")

        event_type = event['type']
        data = event['data']['object']

        # Handle different event types
        if event_type == 'checkout.session.completed':
            logger.info(f"Payment succeeded for session {data['id']}")
            # Here you can add logic to update user's subscription status in your database
        elif event_type == 'customer.subscription.created':
            logger.info(f"Subscription created: {data['id']}")
        elif event_type == 'customer.subscription.updated':
            logger.info(f"Subscription updated: {data['id']}")
        elif event_type == 'customer.subscription.deleted':
            logger.info(f"Subscription canceled: {data['id']}")
            # Here you can add logic to update user's subscription status in your database

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")
