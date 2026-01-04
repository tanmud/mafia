import React, { useState } from "react";
import { usePlayerSocket } from "./usePlayerSocket";

const PlayerView: React.FC = () => {
  const {
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
  } = usePlayerSocket();

  const [name, setName] = useState("");
  const [joined, setJoined] = useState(false);

  const handleJoin = () => {
    if (!name) return;
    joinAsPlayer(name);
    setJoined(true);
  };

  const isGodfather = role === "godfather";
  const isDoctor = role === "doctor";

  const handleMcqClick = (targetId: string) => {
    if (!mcq) return;
    sendMcqAnswer(mcq.questionId, targetId);
  };

  const handleKillClick = (targetId: string) => {
    sendNightKill(targetId);
  };

  const handleSaveClick = (targetId: string) => {
    sendNightSave(targetId);
  };

  const myName = name;

  return (
    <div style={{ padding: 16 }}>
      <h2>Player Client</h2>
      <div>Socket: {connected ? "connected" : "disconnected"}</div>

      {!joined && (
        <div style={{ marginTop: 12 }}>
          <input
            placeholder="Your name"
            value={name}
            onChange={e => setName(e.target.value)}
          />
          <button onClick={handleJoin}>Join as player</button>
          <div>Waiting room count: {waitingCount}</div>
        </div>
      )}

      {roomState && (
        <div style={{ marginTop: 16 }}>
          <div>Room: {roomState.roomId}</div>
          <div>Phase: {roomState.phase}</div>
          {role && <div>Your role: {role}</div>}

          <h3>Players</h3>
          <ul>
            {roomState.players.map(p => (
              <li key={p.id}>
                {p.name} {p.alive ? "" : "(dead)"} {p.name === myName ? "<- you" : ""}
              </li>
            ))}
          </ul>

          {nightResult && (
            <div style={{ marginTop: 8 }}>
              <strong>Night result:</strong>{" "}
              {nightResult.winner
                ? `Winner: ${nightResult.winner}`
                : nightResult.killedId
                ? `Player ${nightResult.killedId} was killed`
                : "No one died"}
            </div>
          )}

          {roomState.phase === "night" && (
            <div style={{ marginTop: 12 }}>
              {mcq && (
                <div style={{ marginBottom: 12 }}>
                  <h4>Fun question</h4>
                  <div>{mcq.text}</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
                    {mcq.options.map(o => (
                      <button key={o.id} onClick={() => handleMcqClick(o.id)}>
                        {o.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {isGodfather && (
                <div style={{ marginBottom: 12 }}>
                  <h4>Choose someone to kill</h4>
                  {roomState.players
                    .filter(p => p.alive && p.name !== myName)
                    .map(p => (
                      <button key={p.id} onClick={() => handleKillClick(p.id)}>
                        Kill {p.name}
                      </button>
                    ))}
                </div>
              )}

              {isDoctor && (
                <div>
                  <h4>Choose someone to save</h4>
                  {roomState.players
                    .filter(p => p.alive)
                    .map(p => (
                      <button key={p.id} onClick={() => handleSaveClick(p.id)}>
                        Save {p.name}
                      </button>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PlayerView;
