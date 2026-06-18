from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

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
async def export_resume(request: ExportRequest):
    try:
        filename_base = get_filename_base(request.markdown_content)

        if request.format == "pdf":
            pdf_bytes = markdown_to_pdf(request.markdown_content)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.pdf"
                },
            )

        elif request.format == "latex_pdf":
            if request.latex_content:
                pdf_bytes = await latex_to_pdf(request.latex_content)
            else:
                pdf_bytes = await markdown_to_latex_pdf(request.markdown_content)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.pdf"
                },
            )

        elif request.format == "latex":
            latex = request.latex_content or md_to_latex(request.markdown_content)
            return Response(
                content=latex.encode("utf-8"),
                media_type="application/x-tex",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.tex"
                },
            )

        elif request.format == "docx":
            docx_buffer = markdown_to_docx(request.markdown_content)
            return StreamingResponse(
                docx_buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.docx"
                },
            )

        elif request.format == "md":
            return Response(
                content=request.markdown_content.encode("utf-8"),
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
