import { useEffect, useState } from "react";
import { controlSocket } from "./sockets";
import type { RoomState } from "./usePlayerSocket";

type WaitingPlayer = { id: string; name: string };

type ControlState = {
  activeRoom: RoomState | null;
  waitingCount: number;
  waitingPlayers: WaitingPlayer[];
};

export function useControlSocket() {
  const [connected, setConnected] = useState(false);
  const [state, setState] = useState<ControlState | null>(null);

  useEffect(() => {
    const s = controlSocket;

    const onConnect = () => setConnected(true);
    const onDisconnect = () => setConnected(false);

    const onControlState = (data: ControlState) => setState(data);

    s.on("connect", onConnect);
    s.on("disconnect", onDisconnect);
    s.on("control_state", onControlState);

    return () => {
      s.off("connect", onConnect);
      s.off("disconnect", onDisconnect);
      s.off("control_state", onControlState);
    };
  }, []);

  const setDoctorEnabled = (enabled: boolean) => {
    controlSocket.emit("control_set_doctor_enabled", { enabled });
  };

  const startGame = () => {
    controlSocket.emit("control_start_game", {});
  };

  const endNight = () => {
    controlSocket.emit("control_end_night", {});
  };

  const startNextNight = () => {
    controlSocket.emit("control_start_next_night", {});
  };

  const resetGame = () => {
    controlSocket.emit("control_reset_game", {});
  };

  return {
    connected,
    state,
    setDoctorEnabled,
    startGame,
    endNight,
    startNextNight,
    resetGame,
  };
}
