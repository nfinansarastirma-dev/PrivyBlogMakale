import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import { Layout } from "@/components/Layout";
import { Home } from "@/pages/Home";
import { Article } from "@/pages/Article";
import { Category } from "@/pages/Category";
import { Search } from "@/pages/Search";
import { AuthCallback } from "@/pages/AuthCallback";
import { Dashboard } from "@/pages/Dashboard";
import { ArticleEditor } from "@/pages/ArticleEditor";

function AppRouter() {
  const location = useLocation();
  // Detect session_id synchronously during render (prevents race conditions)
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/makale/:slug" element={<Article />} />
        <Route path="/kategori/:slug" element={<Category />} />
        <Route path="/arama" element={<Search />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/dashboard/new" element={<ArticleEditor />} />
        <Route path="/dashboard/edit/:id" element={<ArticleEditor />} />
        <Route path="*" element={<Home />} />
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppRouter />
          <Toaster theme="dark" position="top-right" toastOptions={{
            style: { background: "#0A0A0A", border: "1px solid #27272A", color: "#fff", borderRadius: 0 }
          }} />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
