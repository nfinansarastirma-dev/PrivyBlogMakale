import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Lock, Save, Loader2 } from "lucide-react";
import { toast } from "sonner";

export const ResetPassword = () => {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (password !== confirm) return toast.error("Şifreler eşleşmiyor");
    if (password.length < 8) return toast.error("Şifre en az 8 karakter");
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      toast.success("Şifre güncellendi. Giriş yapabilirsiniz.");
      navigate("/login");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Sıfırlama başarısız");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16" data-testid="reset-page">
      <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// auth.reset</div>
      <h1 className="font-outfit font-bold text-4xl md:text-5xl text-white mt-2">Yeni Şifre Belirle</h1>

      {!token ? (
        <div className="mt-6 border border-[#EF4444]/40 bg-[#EF4444]/10 p-4 text-[#EF4444] font-jetbrains text-sm">
          Geçersiz veya eksik token. <Link to="/forgot-password" className="underline">Yeniden isteyin</Link>.
        </div>
      ) : (
        <form onSubmit={submit} className="mt-8 space-y-4">
          <div>
            <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Yeni Şifre</label>
            <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
              <Lock size={16} className="ml-3 text-white/40" />
              <input data-testid="reset-password" type="password" required minLength={8} value={password} onChange={e => setPassword(e.target.value)} className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30" placeholder="••••••••" />
            </div>
          </div>
          <div>
            <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Şifre Tekrar</label>
            <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
              <Lock size={16} className="ml-3 text-white/40" />
              <input data-testid="reset-confirm" type="password" required minLength={8} value={confirm} onChange={e => setConfirm(e.target.value)} className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30" placeholder="••••••••" />
            </div>
          </div>
          <Button type="submit" data-testid="reset-submit" disabled={loading} className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest h-12">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <><Save size={14} className="mr-2" /> Şifreyi Güncelle</>}
          </Button>
        </form>
      )}
    </div>
  );
};
