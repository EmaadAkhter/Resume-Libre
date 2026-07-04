from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from core.limiter import limiter
from schemas.export import ExportRequest
from services.export_utils import (
    markdown_to_pdf,
    markdown_to_docx,
    markdown_to_latex_pdf,
    latex_to_pdf,
    get_filename_base,
)
from services.latex_compiler import md_to_latex

router = APIRouter(tags=["export"])


@router.post("/export-resume")
@limiter.limit("20/hour")
async def export_resume(request: Request, body: ExportRequest):
    try:
        filename_base = get_filename_base(body.markdown_content)

        if body.format == "pdf":
            pdf_bytes = markdown_to_pdf(body.markdown_content)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.pdf"
                },
            )

        elif body.format == "latex_pdf":
            if body.latex_content:
                pdf_bytes = await latex_to_pdf(body.latex_content)
            else:
                pdf_bytes = await markdown_to_latex_pdf(body.markdown_content)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.pdf"
                },
            )

        elif body.format == "latex":
            latex = body.latex_content or md_to_latex(body.markdown_content)
            return Response(
                content=latex.encode("utf-8"),
                media_type="application/x-tex",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.tex"
                },
            )

        elif body.format == "docx":
            docx_buffer = markdown_to_docx(body.markdown_content)
            return StreamingResponse(
                docx_buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.docx"
                },
            )

        elif body.format == "md":
            return Response(
                content=body.markdown_content.encode("utf-8"),
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.md"
                },
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid format")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export resume: {str(e)}"
        )
