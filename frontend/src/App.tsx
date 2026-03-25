import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import AppLayout from './components/Layout/AppLayout';
import ProtectedRoute from './components/Layout/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DocumentList from './pages/Documents/DocumentList';
import DocumentUpload from './pages/Documents/DocumentUpload';
import DocumentDetail from './pages/Documents/DocumentDetail';
import InvoiceReviewList from './pages/Review/InvoiceReviewList';
import InvoiceReview from './pages/Review/InvoiceReview';
import MaterialList from './pages/Materials/MaterialList';
import MaterialDetail from './pages/Materials/MaterialDetail';
import ProviderList from './pages/Providers/ProviderList';
import AnalyticsDashboard from './pages/Analytics/AnalyticsDashboard';
import DestinationList from './pages/Destinations/DestinationList';
import UserList from './pages/Users/UserList';
import { useAuth } from './hooks/useAuth';

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAdmin } = useAuth();
  if (!isAdmin) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="documents" element={<DocumentList />} />
            <Route path="documents/upload" element={<DocumentUpload />} />
            <Route path="documents/:id" element={<DocumentDetail />} />
            <Route path="review" element={<InvoiceReviewList />} />
            <Route path="review/:id" element={<InvoiceReview />} />
            <Route path="materials" element={<MaterialList />} />
            <Route path="materials/:id" element={<MaterialDetail />} />
            <Route path="providers" element={<ProviderList />} />
            <Route path="destinations" element={<DestinationList />} />
            <Route path="analytics" element={<AnalyticsDashboard />} />
            <Route
              path="users"
              element={
                <AdminRoute>
                  <UserList />
                </AdminRoute>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
