import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Mail, Send, Loader2 } from "lucide-react";
import { toast } from "sonner";

export const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [devUrl, setDevUrl] = useState("");
  const [sent, setSent] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/forgot-password", { email });
      setSent(true);
      if (data.dev_reset_url) setDevUrl(data.dev_reset_url);
      toast.success("Sıfırlama linki gönderildi (kayıtlıysa)");
    } catch (err) {
      toast.error("İstek başarısız");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16" data-testid="forgot-page">
      <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// auth.recover</div>
      <h1 className="font-outfit font-bold text-4xl md:text-5xl text-white mt-2">Şifremi Unuttum</h1>
      <p className="mt-3 text-white/60">Email adresinize bir sıfırlama linki göndereceğiz</p>

      <form onSubmit={submit} className="mt-8 space-y-4">
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Email</label>
          <div className="mt-2 flex items-center border border-white/10 focus-within:border-[#F59E0B]">
            <Mail size={16} className="ml-3 text-white/40" />
            <input
              data-testid="forgot-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="flex-1 bg-transparent px-3 py-3 outline-none text-white font-jetbrains text-sm placeholder:text-white/30"
            />
          </div>
        </div>
        <Button type="submit" data-testid="forgot-submit" disabled={loading} className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest h-12">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <><Send size={14} className="mr-2" /> Link Gönder</>}
        </Button>
      </form>

      {sent && (
        <div className="mt-6 border border-[#10B981]/40 bg-[#10B981]/10 p-4 font-jetbrains text-xs text-[#10B981]" data-testid="forgot-sent">
          Eğer bu email kayıtlıysa, sıfırlama linki gönderildi. Gelen kutunuzu kontrol edin.
          {devUrl && (
            <div className="mt-3 pt-3 border-t border-[#10B981]/30 text-white/70 normal-case">
              <p className="text-[10px] uppercase tracking-widest text-white/50 mb-1">Geliştirme modu (SMTP kapalı):</p>
              <Link to={devUrl.replace(window.location.origin, "")} className="text-[#F59E0B] hover:underline break-all">{devUrl}</Link>
            </div>
          )}
        </div>
      )}

      <p className="mt-8 text-center font-jetbrains text-[11px] uppercase tracking-widest text-white/50">
        <Link to="/login" className="text-[#F59E0B] hover:text-white">← Girişe Dön</Link>
      </p>
    </div>
  );
};
