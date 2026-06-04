from fastapi import FastAPI

app = FastAPI(
    title="Agent Knowledge Base",
    description="Semantic knowledge base API with streaming search and MCP integration.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
