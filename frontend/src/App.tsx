import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import CreateDream from "./pages/CreateDream";
import ViewDream from "./pages/ViewDream";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import UserPage from "./pages/UserPage";
import AgentInstructions from "./pages/AgentInstructions";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dreams/create" element={<CreateDream />} />
      <Route path="/dreams/:slug" element={<ViewDream />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Navigate to="/login?mode=signup" replace />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="/users/:username" element={<UserPage />} />
      <Route path="/agent-instructions" element={<AgentInstructions />} />
    </Routes>
  );
}

export default App;
