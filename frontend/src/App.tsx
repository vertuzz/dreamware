import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import CreateApp from "./pages/CreateApp";
import EditApp from "./pages/EditApp";
import ViewApp from "./pages/ViewApp";
import Login from "./pages/Login";
import OAuthCallback from "./pages/OAuthCallback";
import Profile from "./pages/Profile";
import UserPage from "./pages/UserPage";
import AdminPortal from "./pages/AdminPortal";
import AgentInstructions from "./pages/AgentInstructions";
import { usePageTracking } from "./hooks/usePageTracking";

function App() {
  // Track page views on route changes
  usePageTracking();

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/apps/create" element={<CreateApp />} />
      <Route path="/apps/:slug" element={<ViewApp />} />
      <Route path="/apps/:slug/edit" element={<EditApp />} />
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<OAuthCallback />} />
      <Route path="/signup" element={<Navigate to="/login?mode=signup" replace />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="/users/:username" element={<UserPage />} />
      <Route path="/admin" element={<AdminPortal />} />
      <Route path="/admin/claims" element={<Navigate to="/admin" replace />} />
      <Route path="/agent-instructions" element={<AgentInstructions />} />
    </Routes>
  );
}

export default App;
