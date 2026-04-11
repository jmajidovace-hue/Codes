from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.scanners.div_insight import scan_div_insight
from backend.scanners.rebalancing import scan_rebalancing
from backend.charts.div_finder import analyze_dividend_recovery_chart
from backend.charts.rebalance_mapper import analyze_rebalancing_chart
from backend.calculators.trade_calc import calculate_smi, calculate_long_commission

app = FastAPI(title="Trading Insights API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path for the frontend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Route for frontend index
@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Serve the static CSS/JS files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/api/scan/div-insight")
async def run_div_insight_scan():
    """Streams the text output of the dividend insight scan."""
    return StreamingResponse(scan_div_insight(), media_type="text/event-stream")

@app.get("/api/scan/rebalancing")
async def run_rebalancing_scan():
    """Streams the text output of the EOM rebalancing scan."""
    return StreamingResponse(scan_rebalancing(), media_type="text/event-stream")

@app.get("/api/chart/div-finder")
async def get_div_finder_chart(ticker: str):
    """Returns the base64 encoded image for a ticker div analysis."""
    try:
        b64_image = analyze_dividend_recovery_chart(ticker.upper())
        if not b64_image:
            raise HTTPException(status_code=404, detail="Ticker data not found.")
        return {"summary": f"Target Map generated for {ticker.upper()}", "image": b64_image}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chart/rebalance-mapper")
async def get_rebalance_mapper_chart(ticker: str):
    """Returns the base64 encoded image for a ticker rebalancing map."""
    try:
        b64_image = analyze_rebalancing_chart(ticker.upper())
        if not b64_image:
            raise HTTPException(status_code=404, detail="Ticker data not found.")
        return {"summary": f"Rebalancing Map generated for {ticker.upper()}", "image": b64_image}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calc/smi")
async def post_smi_calc(
    ticker: str = Form(...),
    shares: float = Form(...),
    price: float = Form(...),
    days: int = Form(...),
    target_profit: float = Form(...),
    file: UploadFile = File(None)
):
    """Calculates SMI using an uploaded rates file."""
    try:
        content = await file.read() if file else None
        filename = file.filename if file else None
        result = calculate_smi(content, filename, ticker.upper(), shares, price, days, target_profit)
        return {"result": result}
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/calc/long")
async def post_long_calc(
    ticker: str = Form(...),
    shares: float = Form(...),
    price: float = Form(...),
    days: int = Form(...),
    target_profit: float = Form(...)
):
    """Calculates Long Commission."""
    try:
        result = calculate_long_commission(ticker.upper(), shares, price, days, target_profit)
        return {"result": result}
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))
