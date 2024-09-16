main_template = """from pyrails import PyRailsApp
from app.controllers import *


app = PyRailsApp()


@app.on_event("startup")
async def connect_db():
    app.connect_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
