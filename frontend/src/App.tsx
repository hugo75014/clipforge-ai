import { Routes, Route, Navigate } from 'react-router-dom'

import AppShell from './components/layout/AppShell'
import HomeGate from './components/auth/HomeGate'
import ProtectedRoute from './components/auth/ProtectedRoute'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import NewProjectPage from './pages/NewProjectPage'
import ProjectsListPage from './pages/ProjectsListPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import ClipsListPage from './pages/ClipsListPage'
import ClipEditorPage from './pages/ClipEditorPage'
import TemplatesPage from './pages/TemplatesPage'
import BrandKitPage from './pages/BrandKitPage'
import AISettingsPage from './pages/AISettingsPage'
import ExportHistoryPage from './pages/ExportHistoryPage'
import SettingsPage from './pages/SettingsPage'
import AdminPage from './pages/AdminPage'
import LegalNotice from './pages/legal/LegalNotice'
import TermsOfUse from './pages/legal/TermsOfUse'
import PrivacyPolicy from './pages/legal/PrivacyPolicy'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/legal" element={<LegalNotice />} />
      <Route path="/terms" element={<TermsOfUse />} />
      <Route path="/privacy" element={<PrivacyPolicy />} />

      {/* Racine partagée : page de présentation pour un visiteur, application
          pour un compte connecté. Les routes internes restent protégées. */}
      <Route path="/" element={<HomeGate />}>
        <Route index element={<DashboardPage />} />
        <Route path="new" element={<NewProjectPage />} />
        <Route path="projects" element={<ProjectsListPage />} />
        <Route path="projects/:id" element={<ProjectDetailPage />} />
        <Route path="clips" element={<ClipsListPage />} />
        <Route path="clips/:id" element={<ClipEditorPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="brand-kit" element={<BrandKitPage />} />
        <Route path="ai-settings" element={<AISettingsPage />} />
        <Route path="exports" element={<ExportHistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route
          path="admin/*"
          element={
            <ProtectedRoute requireAdmin>
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
