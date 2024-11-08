from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
SCOPES = "read_orders,read_products"  # Adjust as needed
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
                <input type="text" id="shop" name="shop" placeholder="example" required>
                <button type="submit">Install App</button>
            </form>
        </body>
        </html>
        """
    # Remove ".myshopify.com" if it is included
    shop_name = shop.replace(".myshopify.com", "")
    
    # Construct the new OAuth URL using admin.shopify.com
    auth_url = (
        f"https://admin.shopify.com/store/{shop_name}/oauth/request_grant?"
        f"client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@app.post("/")
async def initiate_installation(shop: str = Form(...)):
    shop_name = shop.replace(".myshopify.com", "")
    
    # Construct the new OAuth URL using admin.shopify.com
    auth_url = (
        f"https://admin.shopify.com/store/{shop_name}/oauth/request_grant?"
        f"client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)
