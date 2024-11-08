from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import requests
import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = "read_orders,read_products"
REDIRECT_URI = os.getenv("REDIRECT_URI")

# SQLite setup
conn = sqlite3.connect("shopify_app.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS shop_tokens (shop TEXT PRIMARY KEY, access_token TEXT)''')
conn.commit()

def save_access_token(shop, token):
    """Save the access token in the database."""
    cursor.execute("INSERT OR REPLACE INTO shop_tokens (shop, access_token) VALUES (?, ?)", (shop, token))
    conn.commit()

def get_access_token(shop):
    """Retrieve the access token from the database."""
    cursor.execute("SELECT access_token FROM shop_tokens WHERE shop = ?", (shop,))
    result = cursor.fetchone()
    return result[0] if result else None

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
        save_access_token(shop, access_token)
        return RedirectResponse(url="https://datatram.ai")
    
    return {"error": "Error retrieving access token from Shopify"}
