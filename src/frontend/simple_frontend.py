from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import httpx

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return '''<!DOCTYPE html>
<html><head><title>IMSS Analyzer</title></head>
<body>
    <h1>Analizador IMSS</h1>
    <form id="form">
        <input type="file" id="file" accept=".pdf" required>
        <button type="submit">Analizar</button>
    </form>
    <div id="result"></div>
    <script>
        document.getElementById('form').onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData();
            formData.append('file', document.getElementById('file').files[0]);
            
            const response = await fetch('/upload', {method: 'POST', body: formData});
            const data = await response.json();
            
            document.getElementById('result').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        }
    </script>
</body></html>'''

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    async with httpx.AsyncClient(timeout=30) as client:
        files = {"file": (file.filename, await file.read(), "application/pdf")}
        response = await client.post("http://localhost:8001/parse", files=files)
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)

