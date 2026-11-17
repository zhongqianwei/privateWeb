"""一键启动后端：venv\Scripts\python.exe run.py（默认托管 frontend/dist 一体化访问）"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
