import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { api, API } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Mail, Lock, LogIn, Loader2 } from "lucide-react";
import { toast } from "sonner";

export const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { loginWithToken, googleEnabled } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const params = new URLSearchParams(location.search);
  const errorParam = params.get("error");

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      await loginWithToken(data.access_token);
      toast.success("Giriş başarılı");
      navigate(data.user.role === "admin" ? "/dashboard" : "/");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Giriş yapılamadı");
    } finally {
      setLoading(false);
    }
  };

  const googleLogin = () => {
    window.location.href = `${API}/auth/google/login`;
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16" data-testid="login-page">
      <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// auth.login</div>
      <h1 className="font-outfit font-bold text-4xl md:text-5xl text-white mt-2">Giriş Yap</h1>
      <p className="mt-3 text-white/60">PrivyAlgo Blog panelinize erişin</p>

      {errorParam && (
        <div className="mt-6 border border-[#EF4444]/40 bg-[#EF4444]/10 p-3 font-jetbrains text-[11px] uppercase tracking-widest text-[#EF4444]" data-testid="login-error">
          {errorParam === "google_auth_failed" ? "Google girişi başarısız" : errorParam === "google_no_email" ? "Google email alınamadı" : "Bir hata oluştu"}
        </div>
      )}

      <form onSubmit={submit} className="mt-8 space-y-4">
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Email</label>
          <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
            <Mail size={16} className="ml-3 text-white/40" />
            <input
              data-testid="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="admin@example.com"
              className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30"
            />
          </div>
        </div>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Şifre</label>
          <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
            <Lock size={16} className="ml-3 text-white/40" />
            <input
              data-testid="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30"
            />
          </div>
          <Link to="/forgot-password" data-testid="forgot-link" className="mt-2 inline-block font-jetbrains text-[10px] uppercase tracking-widest text-white/50 hover:text-[#F59E0B]">
            Şifremi Unuttum
          </Link>
        </div>

        <Button
          type="submit"
          data-testid="login-submit"
          disabled={loading}
          className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest h-12"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <><LogIn size={14} className="mr-2" /> Giriş Yap</>}
        </Button>
      </form>

      {googleEnabled && (
        <>
          <div className="mt-8 flex items-center gap-4">
            <div className="flex-1 h-px bg-white/10" />
            <span className="font-jetbrains text-[10px] uppercase tracking-widest text-white/40">ya da</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>
          <button
            data-testid="google-login-btn"
            onClick={googleLogin}
            className="mt-6 w-full flex items-center justify-center gap-3 border border-white/20 hover:border-[#F59E0B] hover:text-[#F59E0B] text-white h-12 font-jetbrains text-[11px] uppercase tracking-widest transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
            Google ile Giriş Yap
          </button>
        </>
      )}

      <p className="mt-8 text-center font-jetbrains text-[11px] uppercase tracking-widest text-white/50">
        Hesabın yok mu?{" "}
        <Link to="/register" data-testid="register-link" className="text-[#F59E0B] hover:text-white">Kayıt Ol</Link>
      </p>
    </div>
  );
};
