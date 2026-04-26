import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/ProtectedRoute";
import ComparisonPage from "./pages/ComparisonPage";
import DashboardPage from "./pages/DashboardPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import HomePage from "./pages/HomePage";
import ImpactEnginePage from "./pages/ImpactEnginePage";
import LoginPage from "./pages/LoginPage";
import MatchAnalyzerPage from "./pages/MatchAnalyzerPage";
import PipelinePanelPage from "./pages/PipelinePanelPage";
import RegisterPage from "./pages/RegisterPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import ScoutReportsPage from "./pages/ScoutReportsPage";
import SmartRecommendationPage from "./pages/SmartRecommendationPage";
import TransferMarketPage from "./pages/TransferMarketPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import WatchlistPage from "./pages/WatchlistPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/watchlist"
        element={
          <ProtectedRoute>
            <WatchlistPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/comparison"
        element={
          <ProtectedRoute>
            <ComparisonPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recommendations"
        element={
          <ProtectedRoute>
            <SmartRecommendationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/impact"
        element={
          <ProtectedRoute>
            <ImpactEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/transfer-market"
        element={
          <ProtectedRoute>
            <TransferMarketPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pipeline"
        element={
          <ProtectedRoute>
            <PipelinePanelPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/scout-reports"
        element={
          <ProtectedRoute>
            <ScoutReportsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/match-analyzer"
        element={
          <ProtectedRoute>
            <MatchAnalyzerPage />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
