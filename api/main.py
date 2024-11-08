from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local testing)
load_dotenv()

app = FastAPI()

# Fetch credentials from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = "read_orders"
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.get("/", response_class=HTMLResponse)
async def home():
    return '''
        <h1>Connect your Shopify store</h1>
        <form action="/connect" method="GET">
            <input type="text" name="shop" placeholder="example.myshopify.com" required>
            <button type="submit">Connect Shopify</button>
        </form>
    '''

@app.get("/connect")
async def connect_shopify(shop: str):
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(code: str, shop: str):
    # Exchange the authorization code for an access token
    access_token_response = requests.post(
        f"https://{shop}/admin/oauth/access_token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        }
    )

    if access_token_response.status_code != 200:
        return {"error": "Error retrieving access token from Shopify"}

    access_token = access_token_response.json().get('access_token')
    
    if not access_token:
        return {"error": "Failed to retrieve access token from Shopify"}

    # Fetch store information using the access token
    headers = {
        "X-Shopify-Access-Token": access_token
    }
    store_info_response = requests.get(f"https://{shop}/admin/api/2023-04/shop.json", headers=headers)
    
    if store_info_response.status_code != 200:
        return {"error": "Error retrieving store information from Shopify"}
    
    store_info = store_info_response.json().get("shop", {})

    # Transform the response to match the desired format
    return {
        "message": "Successfully connected to Shopify",
        "hostname": store_info.get("myshopify_domain"),
        "password": access_token,
        "api_key": CLIENT_ID
    }
