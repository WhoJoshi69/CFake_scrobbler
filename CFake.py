import os
import re
import requests
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import concurrent.futures  # Added for threading

app = FastAPI()

# Define the templates folder
templates = Jinja2Templates(directory="templates")

# Store active WebSocket connections
websocket_connections = []

executor = concurrent.futures.ThreadPoolExecutor()


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


# Function to send messages to all connected clients
async def send_message(message):
    for connection in websocket_connections:
        await connection.send_text(message)


# Modify your print statements to send messages to the frontend
def print_to_frontend(message):
    print(message)  # Print to console as well
    asyncio.run(send_message(message))


@app.get("/fetch_everything/")
def fetch_everything(url):
    index = 1
    page_index = 1
    main_url = url
    name = main_url.split("/")[5].replace("%20", " ")
    print(f"Fetching images of {name}")
    while True:
        page_url = f'{main_url}/p{page_index}'
        response = requests.get(page_url)

        if response.status_code == 200:
            input_string = response.text
        else:
            break

        # Regular expression pattern to match the image URLs
        pattern = r"showimage\(\'([^']+)'"

        # Find all matches of the pattern in the input string
        matches = re.findall(pattern, input_string)

        # Base URL for the images
        base_url = "https://www.cfake.com/medias/photos/"
        image_urls = []
        # Create the array of image URLs
        celeb_name = main_url.split("/")[5].replace("_", " ")
        if celeb_name not in matches[0]:
            break
        for match in matches:
            if celeb_name in match:
                match = match.replace('big.php?show=', '').split('&')[0]
                image_urls.append(base_url + match)

        # Output folder where images will be saved
        output_folder = f"C:\Darshit\Fakes\{name}"

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Define a function to download images
        def download_image(url, index):
            response = requests.get(url)
            if response.status_code == 200:
                image_extension = url.split('.')[-1]
                image_filename = f"image_{index}.{image_extension}"
                image_path = os.path.join(output_folder, image_filename)

                with open(image_path, 'wb') as image_file:
                    image_file.write(response.content)

                print(f"Downloaded: {image_filename}")
            else:
                print(f"Failed to download: {url}")

        # Download images using multiple threads
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for url in image_urls:
                executor.submit(download_image, url, index)
                index += 1

        print(f"Page {page_index} completed successfully")
        page_index += 1

    print(f"Completed fetching for {name}")
    return f"Completed fetching for {name}"
