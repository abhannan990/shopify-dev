from fastapi import FastAPI, Request, HTTPException 
from fastapi.responses import RedirectResponse
import httpx
import os

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = "read_orders"
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.get("/auth")
async def auth():
    shopify_auth_url = (
        f"https://{YOUR_SHOP_NAME}.myshopify.com/admin/oauth/authorize?"
        f"client_id={CLIENT_ID}&scope=read_products,write_products&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(shopify_auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    token_url = f"https://{YOUR_SHOP_NAME}.myshopify.com/admin/oauth/access_token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        access_token = response.json().get("access_token")

    # Store access_token securely and redirect to the app's main interface
    # Assuming you have some way of managing sessions for authenticated users
    return RedirectResponse("https://datatram.ai/dashboard")

# Additional routes and logic for your app
