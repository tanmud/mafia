import React from "react";
import { useControlSocket } from "./useControlSocket";

const ControlView: React.FC = () => {
  const {
    connected,
    state,
    setDoctorEnabled,
    startGame,
    endNight,
    startNextNight,
    resetGame,
  } = useControlSocket();

  const room = state?.activeRoom || null;
  const waitingPlayers = state?.waitingPlayers || [];
  const doctorEnabled = room?.doctorEnabled ?? false;

  return (
    <div style={{ padding: 16, borderLeft: "1px solid #ccc" }}>
      <h2>Control Panel</h2>
      <div>Socket: {connected ? "connected" : "disconnected"}</div>

      <div style={{ marginTop: 12 }}>
        <div>Waiting players: {state?.waitingCount ?? 0}</div>
        <ul>
          {waitingPlayers.map(p => (
            <li key={p.id}>{p.name}</li>
          ))}
        </ul>
      </div>

      {room && (
        <div style={{ marginTop: 12 }}>
          <div>Active room: {room.roomId}</div>
          <div>Phase: {room.phase}</div>
          <div>Night round: {room.nightRound}</div>
          <label>
            <input
              type="checkbox"
              checked={doctorEnabled}
              onChange={() => setDoctorEnabled(!doctorEnabled)}
            />
            Include doctor role
          </label>

          <h3>Players in game</h3>
          <ul>
            {room.players.map(p => (
              <li key={p.id}>
                {p.name} {p.alive ? "" : "(dead)"} {p.isHost ? "(host)" : ""}
              </li>
            ))}
          </ul>

          <div style={{ marginTop: 8 }}>
            <button onClick={startGame}>Start game (auto assign & move waiting)</button>
          </div>
          <div style={{ marginTop: 8 }}>
            <button onClick={endNight}>End night</button>
            <button onClick={startNextNight} style={{ marginLeft: 8 }}>
              Start next night
            </button>
          </div>
          <div style={{ marginTop: 8 }}>
            <button onClick={resetGame}>Reset game</button>
          </div>
        </div>
      )}

      {!room && (
        <div style={{ marginTop: 12 }}>
          <div>No active room yet. Start game will create one when players join.</div>
        </div>
      )}
    </div>
  );
};

export default ControlView;
