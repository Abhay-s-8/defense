import { Navigate, Route, Routes } from "react-router-dom";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Predict from "./pages/Predict";
import RedTeam from "./pages/RedTeam";
import Metrics from "./pages/Metrics";
import GenAILab from "./pages/GenAILab";

import Shell from "./components/Shell";


function ProtectedRoute({ children }) {
  const token =
    localStorage.getItem("mastercard_token");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}


function ProtectedPage({ children }) {
  return (
    <ProtectedRoute>
      <Shell>
        {children}
      </Shell>
    </ProtectedRoute>
  );
}


export default function App() {
  return (
    <Routes>

      <Route
        path="/"
        element={<Landing />}
      />

      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedPage>
            <Dashboard />
          </ProtectedPage>
        }
      />

      <Route
        path="/predict"
        element={
          <ProtectedPage>
            <Predict />
          </ProtectedPage>
        }
      />

      <Route
        path="/red-team"
        element={
          <ProtectedPage>
            <RedTeam />
          </ProtectedPage>
        }
      />

      <Route
        path="/metrics"
        element={
          <ProtectedPage>
            <Metrics />
          </ProtectedPage>
        }
      />


      <Route
        path="/genai"
        element={
          <ProtectedPage>
            <GenAILab />
          </ProtectedPage>
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />

    </Routes>
  );
}