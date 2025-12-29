import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import CreateDream from "./pages/CreateDream";
import ViewDream from "./pages/ViewDream";
import Login from "./pages/Login";
import Profile from "./pages/Profile";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dreams/create" element={<CreateDream />} />
      <Route path="/dreams/:id" element={<ViewDream />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Navigate to="/login?mode=signup" replace />} />
      <Route path="/profile" element={<Profile />} />
    </Routes>
  );
}

export default App;
