import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from sockets import register_socket_handlers

IPV4 = "192.168.0.45"

fastapi_app = FastAPI()

origins = [
    f"http://{IPV4}:3000",
    f"http://{IPV4}:8000",
]

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fastapi_app.get("/health")
async def health_check():
    return {"status": "ok"}

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=origins)
register_socket_handlers(sio)
app = socketio.ASGIApp(sio, fastapi_app)

if __name__ == "__main__":
    uvicorn.run(app, host=IPV4, port=8000)