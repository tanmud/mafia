import { io, Socket } from "socket.io-client";

const BASE_URL =
  import.meta.env.VITE_MAFIA_BASE_URL || "http://localhost:8000";

console.log("BASE_URL =", BASE_URL);

export const playerSocket: Socket = io(BASE_URL, {
  path: "/socket.io/",
  transports: ["websocket"],
});

export const controlSocket: Socket = io(`${BASE_URL}/control`, {
  path: "/socket.io/",
  transports: ["websocket"],
});
