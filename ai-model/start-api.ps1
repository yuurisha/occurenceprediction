# Quick Start Script for AI Dashboard

Write-Host "=====================================" -ForegroundColor Green
Write-Host "AI-Powered Dashboard Quick Start" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Check if model files exist
$modelPath = "c:\Users\Yourisha\Documents\SEM 6\florai\ai-model\occurrence_model.pkl"
if (-not (Test-Path $modelPath)) {
    Write-Host "❌ Model files not found!" -ForegroundColor Red
    Write-Host "Please run the Jupyter notebook first to train the model." -ForegroundColor Yellow
    Write-Host "File: ai-model/occurrence_prediction_model.ipynb" -ForegroundColor Yellow
    exit
}

Write-Host "✓ Model files found" -ForegroundColor Green

# Start AI Model API
Write-Host ""
Write-Host "Starting AI Model API on http://localhost:8000..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Yellow
Write-Host ""

cd "c:\Users\Yourisha\Documents\SEM 6\florai\ai-model"
& "C:/Users/Yourisha/Documents/SEM 6/florai/florai/model_server/.venv/Scripts/python.exe" api.py
