import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from sockets import register_socket_handlers

# IP passed from run_game.sh, e.g. 192.168.1.101
LAN_IP = os.getenv("MAFIA_LAN_IP", "localhost")
BACKEND_PORT = int(os.getenv("MAFIA_BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("MAFIA_FRONTEND_PORT", "3000"))

fastapi_app = FastAPI()

# origins = [
#     # local dev
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     f"http://localhost:{FRONTEND_PORT}",
#     f"http://127.0.0.1:{FRONTEND_PORT}",

#     # LAN (from env)
#     f"http://{LAN_IP}:{FRONTEND_PORT}",
#     f"http://{LAN_IP}:{BACKEND_PORT}",
# ]

origins = ["*"] 

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fastapi_app.get("/health")
async def health():
    return {"status": "ok", "lan_ip": LAN_IP, "backend_port": BACKEND_PORT}


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=origins,
)
register_socket_handlers(sio)

app = socketio.ASGIApp(sio, fastapi_app)


if __name__ == "__main__":
    # For manual runs; the script also passes ports via env
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=True,
    )
