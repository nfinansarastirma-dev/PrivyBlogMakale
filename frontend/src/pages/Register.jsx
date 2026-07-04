import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Mail, Lock, User, UserPlus, Loader2 } from "lucide-react";
import { toast } from "sonner";

export const Register = () => {
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      toast.error("Şifreler eşleşmiyor");
      return;
    }
    if (form.password.length < 8) {
      toast.error("Şifre en az 8 karakter olmalı");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/auth/register", { name: form.name, email: form.email, password: form.password });
      await loginWithToken(data.access_token);
      toast.success("Kayıt tamam");
      navigate("/");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Kayıt yapılamadı");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16" data-testid="register-page">
      <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// auth.register</div>
      <h1 className="font-outfit font-bold text-4xl md:text-5xl text-white mt-2">Kayıt Ol</h1>
      <p className="mt-3 text-white/60">Yeni bir hesap oluşturun</p>

      <form onSubmit={submit} className="mt-8 space-y-4">
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Ad Soyad</label>
          <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
            <User size={16} className="ml-3 text-white/40" />
            <input data-testid="register-name" required value={form.name} onChange={e => set("name", e.target.value)} className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30" placeholder="John Doe" />
          </div>
        </div>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Email</label>
          <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
            <Mail size={16} className="ml-3 text-white/40" />
            <input data-testid="register-email" type="email" required value={form.email} onChange={e => set("email", e.target.value)} className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30" placeholder="you@example.com" />
          </div>
        </div>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Şifre <span className="text-white/40 normal-case">(en az 8 karakter)</span></label>
          <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
            <Lock size={16} className="ml-3 text-white/40" />
            <input data-testid="register-password" type="password" required minLength={8} value={form.password} onChange={e => set("password", e.target.value)} className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30" placeholder="••••••••" />
          </div>
        </div>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Şifre Tekrar</label>
          <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
            <Lock size={16} className="ml-3 text-white/40" />
            <input data-testid="register-confirm" type="password" required minLength={8} value={form.confirm} onChange={e => set("confirm", e.target.value)} className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30" placeholder="••••••••" />
          </div>
        </div>

        <Button type="submit" data-testid="register-submit" disabled={loading} className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest h-12">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <><UserPlus size={14} className="mr-2" /> Hesap Oluştur</>}
        </Button>
      </form>

      <p className="mt-8 text-center font-jetbrains text-[11px] uppercase tracking-widest text-white/50">
        Hesabın var mı?{" "}
        <Link to="/login" data-testid="login-link" className="text-[#F59E0B] hover:text-white">Giriş Yap</Link>
      </p>
    </div>
  );
};
