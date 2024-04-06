import json
import os
import re
import requests
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import pandas as pd

from starlette.websockets import WebSocketDisconnect

app = FastAPI()

# Define the templates folder
templates = Jinja2Templates(directory="templates")

# Store active WebSocket connections
websocket_connections = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        while True:
            await asyncio.sleep(1)  # Keep the connection alive
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


# Rest of your code for fetching images remains the same

# Function to send messages to all connected clients
async def send_message(message):
    for connection in websocket_connections:
        await connection.send_text(message)


# Modify your print statements to send messages to the frontend
def print_to_frontend(message):
    print(message)  # Print to console as well
    asyncio.run(send_message(message))


game_data = {}

@app.get("/fetch_everything/")
def fetch_everything(url):
    global game_data
    index = 1
    page_index = 1
    main_url = url
    seen_titles = set()  # Set to keep track of encountered titles
    print(f"Fetching all completed games list")

    while True:
        page_url = main_url + f"/page/{page_index}"
        response = requests.get(page_url)

        # Break the loop if the status code is 404
        if response.status_code == 404:
            print(f"Page {page_index} not found. Exiting the loop.")
            break

        # Extract titles and image URLs using regex
        titles = re.findall(r'rk" title="([^"]+)"', response.text)
        image_urls = re.findall(r'data-bg="([^"]+)"', response.text)

        # Combine titles and image URLs into a nested dictionary, avoiding duplicates
        page_data = {title: {"Title": title, "Image URL": image_url} for title, image_url in zip(titles, image_urls) if title not in seen_titles}
        seen_titles.update(titles)  # Update the set with new titles
        game_data.update(page_data)
        print(f"page_data collected for page {page_index}")
        page_index += 1

        # Break the loop if there are no more pages
        if "No more pages" in response.text:
            break

    # Create a DataFrame from the collected data
    df = pd.DataFrame(list(game_data.values()))

    # Add a new column with the formula "=IMAGE(url, 1)"
    df["Image Formula"] = df["Image URL"].apply(lambda x: f'=IMAGE("{x}", 1)')

    # Save the updated DataFrame to an Excel file
    df.to_excel("game_data_with_images.xlsx", index=False)

    return {"Done :) Enjoy!"}
