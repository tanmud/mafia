import ControlPanel from "./ControlView";
import PlayerView from "./PlayerView";

function App() {
  const params = new URLSearchParams(window.location.search);
  const role = params.get("role") || "player";

  if (role === "control") {
    return <ControlPanel />;
  }

  return <PlayerView />;
}

export default App;
