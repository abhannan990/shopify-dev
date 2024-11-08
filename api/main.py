from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
SCOPES = "read_orders,read_products"  # Specify the scopes you need
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.get("/", response_class=HTMLResponse)
async def install_page(request: Request):
    shop = request.query_params.get("shop")
    if not shop:
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head><title>Install Data Tram App</title></head>
        <body>
            <form action="/" method="post">
                <label for="shop">Enter your Shopify store domain:</label>
                <input type="text" id="shop" name="shop" placeholder="example.myshopify.com" required>
                <button type="submit">Install App</button>
            </form>
        </body>
        </html>
        """
    # Construct the OAuth URL and redirect the user
    auth_url = f"https://{shop}/admin/oauth/authorize?client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    return RedirectResponse(url=auth_url)

@app.post("/")
async def initiate_installation(shop: str = Form(...)):
    # Redirect to Shopify's OAuth page with the shop domain
    auth_url = f"https://{shop}/admin/oauth/authorize?client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(code: str, shop: str):
    access_token_response = requests.post(
        f"https://{shop}/admin/oauth/access_token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": os.getenv("CLIENT_SECRET"),
            "code": code
        }
    )
    if access_token_response.status_code == 200:
        access_token = access_token_response.json().get('access_token')
        return RedirectResponse(url="https://datatram.ai")
    return {"error": "Error retrieving access token from Shopify"}
