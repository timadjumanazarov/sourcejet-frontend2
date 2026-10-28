import os
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sourcejet_report import build_pdf_report
from supabase import create_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Очищаем от случайных пробелов
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

print(f"DEBUG: SUPABASE_URL = '{SUPABASE_URL}'")
print(f"DEBUG: SUPABASE_KEY length = {len(SUPABASE_KEY)}")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("ОШИБКА: SUPABASE_URL или SUPABASE_KEY не заданы в Environment на Render!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/api/download-report/{inspection_id}")
async def download_report(inspection_id: str):
    try:
        response = supabase.table("inspections").select("*").eq("id", inspection_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Inspection not found")
        
        inspection_data = response.data[0]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf_path = tmp_file.name

        build_pdf_report(inspection_data, pdf_path)

        filename = f"SourceJet-Report-{inspection_id[:8]}.pdf"
        return FileResponse(path=pdf_path, filename=filename, media_type="application/pdf")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
