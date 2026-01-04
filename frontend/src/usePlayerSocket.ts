import { useEffect, useState } from "react";
import { playerSocket } from "./sockets";

export type Player = {
  id: string;
  name: string;
  alive: boolean;
  isHost: boolean;
};

export type RoomState = {
  roomId: string;
  phase: "lobby" | "night" | "day" | "ended";
  doctorEnabled: boolean;
  nightRound: number;
  players: Player[];
};

export type McqQuestion = {
  questionId: string;
  text: string;
  options: { id: string; name: string; alive: boolean }[];
};

export function usePlayerSocket() {
  const [connected, setConnected] = useState(false);
  const [roomState, setRoomState] = useState<RoomState | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [mcq, setMcq] = useState<McqQuestion | null>(null);
  const [nightResult, setNightResult] = useState<any>(null);
  const [waitingCount, setWaitingCount] = useState(0);

  useEffect(() => {
    const s = playerSocket;

    const onConnect = () => setConnected(true);
    const onDisconnect = () => setConnected(false);

    const onRoomState = (state: RoomState) => setRoomState(state);
    const onRoleInfo = (data: { role: string }) => setRole(data.role);
    const onPhaseChange = (data: { roomId: string; phase: RoomState["phase"] }) => {
      setRoomState(prev => (prev ? { ...prev, phase: data.phase } : prev));
    };
    const onMcqQuestion = (data: McqQuestion) => {
      setMcq(data);
    };
    const onNightResult = (data: any) => setNightResult(data);
    const onWaitingCount = (data: { count: number }) => setWaitingCount(data.count);

    s.on("connect", onConnect);
    s.on("disconnect", onDisconnect);
    s.on("room_state", onRoomState);
    s.on("role_info", onRoleInfo);
    s.on("phase_change", onPhaseChange);
    s.on("mcq_question", onMcqQuestion);
    s.on("night_result", onNightResult);
    s.on("waiting_count", onWaitingCount);

    return () => {
      s.off("connect", onConnect);
      s.off("disconnect", onDisconnect);
      s.off("room_state", onRoomState);
      s.off("role_info", onRoleInfo);
      s.off("phase_change", onPhaseChange);
      s.off("mcq_question", onMcqQuestion);
      s.off("night_result", onNightResult);
      s.off("waiting_count", onWaitingCount);
    };
  }, []);

  const joinAsPlayer = (name: string) => {
    playerSocket.emit("join_player", { name });
  };

  const sendNightKill = (targetId: string) => {
    playerSocket.emit("night_kill", { targetId });
  };

  const sendNightSave = (targetId: string) => {
    playerSocket.emit("night_save", { targetId });
  };

  const sendMcqAnswer = (questionId: string, targetId: string) => {
    playerSocket.emit("mcq_answer", { questionId, targetId });
  };

  return {
    connected,
    roomState,
    role,
    mcq,
    nightResult,
    waitingCount,
    joinAsPlayer,
    sendNightKill,
    sendNightSave,
    sendMcqAnswer,
  };
}
