from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import config
from routers import task

app = FastAPI(
    title="EduOrchestra",
    description="多智能体驱动的 K12 数学自主学习系统",
    version="0.1.0",
)

# CORS: 允许前端开发服务器跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(task.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
