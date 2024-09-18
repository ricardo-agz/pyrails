main_template = """from pyrails import PyRailsApp
from contextlib import asynccontextmanager
from app.controllers import *


@asynccontextmanager
async def lifespan(app: PyRailsApp):
    app.connect_db()
    yield


app = PyRailsApp(lifespan=lifespan)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
