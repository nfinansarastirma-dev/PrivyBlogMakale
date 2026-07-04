import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { ForgotPassword } from "@/pages/ForgotPassword";
import { ResetPassword } from "@/pages/ResetPassword";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Layout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/makale/:slug" element={<Article />} />
              <Route path="/kategori/:slug" element={<Category />} />
              <Route path="/arama" element={<Search />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/dashboard/new" element={<ArticleEditor />} />
              <Route path="/dashboard/edit/:id" element={<ArticleEditor />} />
              <Route path="*" element={<Home />} />
            </Routes>
          </Layout>
          <Toaster theme="dark" position="top-right" toastOptions={{
            style: { background: "#0A0A0A", border: "1px solid #27272A", color: "#fff", borderRadius: 0 }
          }} />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
