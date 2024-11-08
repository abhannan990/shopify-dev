from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import requests
import os
from databases import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Shopify credentials from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = "read_orders,read_products"
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()

@app.on_event("shutdown")
async def shutdown():
    if database.is_connected:
        await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def initiate_installation(request: Request):
    shop = request.query_params.get("shop")
    if not shop:
        return HTMLResponse("<h1>Missing 'shop' parameter in the URL.</h1>", status_code=400)

    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    shop = request.query_params.get("shop")
    if not code or not shop:
        return {"error": "Required parameters missing"}

    token_response = requests.post(
        f"https://{shop}/admin/oauth/access_token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        }
    )

    if token_response.status_code == 200:
        access_token = token_response.json().get('access_token')
        await save_access_token(shop, access_token)
        return {"message": "Successfully authenticated with Shopify!"}

    return {"error": "Failed to get access token from Shopify"}

# Save access token to MySQL
async def save_access_token(shop: str, token: str):
    if not database.is_connected:
        await database.connect()
        
    query = """
    INSERT INTO shop_tokens (shop, access_token)
    VALUES (:shop, :access_token)
    ON DUPLICATE KEY UPDATE access_token = VALUES(access_token)
    """
    await database.execute(query, {"shop": shop, "access_token": token})
