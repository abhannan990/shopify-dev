from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = "read_orders,read_products"  # Define scopes based on your needs
REDIRECT_URI = os.getenv("REDIRECT_URI")

# HTML template with CSS for the installation form
INSTALL_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Install Data Tram App</title>
    <style>
        body {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f0f0f5;
        }
        .container {
            max-width: 400px;
            padding: 2em;
            background-color: #ffffff;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            text-align: center;
        }
        h1 {
            font-size: 1.5em;
            color: #333333;
        }
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 0.5em;
        }
        input[type="text"] {
            width: 100%;
            padding: 0.8em;
            margin-bottom: 1em;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        button {
            padding: 0.8em 2em;
            background-color: #4CAF50;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            font-size: 1em;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Connect Your Shopify Store</h1>
        <form action="/install" method="post">
            <label for="shop">Enter your Shopify store domain:</label>
            <input type="text" id="shop" name="shop" placeholder="example.myshopify.com" required>
            <button type="submit">Install App</button>
        </form>
    </div>
</body>
</html>
"""

@app.get("/install", response_class=HTMLResponse)
async def install_page(request: Request):
    shop = request.query_params.get("shop")
    if not shop:
        # Display form if shop parameter is missing
        return INSTALL_FORM_HTML
    # Redirect to the Shopify OAuth URL if the shop domain is provided
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={CLIENT_ID}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@app.post("/install")
async def initiate_installation(shop: str = Form(...)):
    # Redirect to Shopify's OAuth page with the shop domain
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

    # Here you can save the access_token to a secure database with the shop domain for future API calls

    # Redirect the user to the main Data Tram website after successful connection
    return RedirectResponse(url="https://datatram.ai")
