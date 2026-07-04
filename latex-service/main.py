import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="Tectonic LaTeX Service")


class CompileRequest(BaseModel):
    latex: str


@app.post("/compile")
def compile(req: CompileRequest) -> Response:
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "resume.tex"
        tex_path.write_text(req.latex, encoding="utf-8")

        result = subprocess.run(
            ["tectonic", str(tex_path), "--outdir", tmpdir],
            capture_output=True,
            text=True,
            timeout=300,
        )

        pdf_path = Path(tmpdir) / "resume.pdf"
        if not pdf_path.exists():
            raise HTTPException(status_code=500, detail=result.stderr or "Compilation failed")

        return Response(pdf_path.read_bytes(), media_type="application/pdf")


@app.get("/health")
def health():
    return {"status": "ok"}
