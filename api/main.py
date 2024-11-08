from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from databases import Database
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Shopify credentials from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = "read_orders,read_products"
REDIRECT_URI = os.getenv("REDIRECT_URI")

# MySQL database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create a Database connection
database = Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Save access token to MySQL
async def save_access_token(shop, token):
    query = """
    INSERT INTO shop_tokens (shop, access_token)
    VALUES (:shop, :access_token)
    ON DUPLICATE KEY UPDATE access_token = VALUES(access_token)
    """
    await database.execute(query, values={"shop": shop, "access_token": token})

# Retrieve access token from MySQL
async def get_access_token(shop):
    query = "SELECT access_token FROM shop_tokens WHERE shop = :shop"
    result = await database.fetch_one(query, values={"shop": shop})
    return result["access_token"] if result else None

@app.get("/", response_class=HTMLResponse)
async def initiate_installation(request: Request):
    shop = request.query_params.get("shop")
    if not shop:
        raise HTTPException(status_code=400, detail="Missing 'shop' parameter")
    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"
    
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(code: str, shop: str):
    """Handle Shopify's callback and store the access token."""
    access_token_response = requests.post(
        f"https://{shop}/admin/oauth/access_token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        }
    )

    if access_token_response.status_code == 200:
        access_token = access_token_response.json().get('access_token')
        await save_access_token(shop, access_token)
        return RedirectResponse(url="https://datatram.ai")
    
    return {"error": "Error retrieving access token from Shopify"}

@app.get("/test-shopify-api")
async def test_shopify(shop: str):
    """Endpoint to test access to Shopify store data."""
    access_token = await get_access_token(shop)
    if not access_token:
        return {"error": "Access token not found for this shop"}
    
    headers = {
        "X-Shopify-Access-Token": access_token
    }
    response = requests.get(f"https://{shop}/admin/api/2023-04/shop.json", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to retrieve shop data", "details": response.json()}
