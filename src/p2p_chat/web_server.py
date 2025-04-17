# src/p2p_chat/web_server.py
import os
import argparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pkg_resources

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you may want to restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the path to the frontend files within the package
try:
    frontend_dir = pkg_resources.resource_filename('p2p_chat', 'frontend')
except:
    # Fallback for development mode
    package_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(package_dir, 'frontend')

if not os.path.exists(frontend_dir):
    os.makedirs(frontend_dir)

# Serve static files
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    try:
        html_path = os.path.join(frontend_dir, "index.html")
        return FileResponse(html_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend files not found")

@app.get("/App.js")
async def read_js():
    """Serve the App.js file."""
    try:
        js_path = os.path.join(frontend_dir, "App.js")
        return FileResponse(js_path, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="App.js not found")

@app.get("/App.css")
async def read_css():
    """Serve the App.css file."""
    try:
        css_path = os.path.join(frontend_dir, "App.css")
        return FileResponse(css_path, media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="App.css not found")

def main(host="127.0.0.1", port=3000):
    """Run the web server."""
    uvicorn.run(app, host=host, port=port)

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='P2P Chat Web Server')
    parser.add_argument('--host', default="127.0.0.1", help='Web server host')
    parser.add_argument('--port', type=int, default=3000, help='Web server port')
    args = parser.parse_args()
    
    main(args.host, args.port)

if __name__ == "__main__":
    main_entry()