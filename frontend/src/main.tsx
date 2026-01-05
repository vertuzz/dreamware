import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { AppCacheProvider } from "./contexts/AppCacheContext";
import { initializeGA } from "./lib/analytics";
import "~/styles/globals.css";
import App from "./App.tsx";

// Initialize Google Analytics
initializeGA();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AppCacheProvider>
          <App />
        </AppCacheProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
