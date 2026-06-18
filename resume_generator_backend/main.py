from dotenv import load_dotenv

load_dotenv()

from core.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    print("Resume-Libre API v2.1.0 — http://localhost:8000")
    print("Docs — http://localhost:8000/docs")
    print("Debug — http://localhost:8000/debug/events")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=4)
