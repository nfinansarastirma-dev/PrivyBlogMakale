import { Lock, Mail } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export const EducationGate = ({ compact = false }) => {
  const { user } = useAuth();
  const startLogin = () => {
    window.location.href = "/login";
  };

  return (
    <div
      data-testid="education-gate"
      className="relative border border-[#F59E0B]/40 bg-gradient-to-br from-[#F59E0B]/10 via-black to-black p-8 md:p-14 overflow-hidden"
    >
      <div className="absolute top-0 left-0 w-24 h-24 border-l-2 border-t-2 border-[#F59E0B]/60" />
      <div className="absolute bottom-0 right-0 w-24 h-24 border-r-2 border-b-2 border-[#F59E0B]/60" />

      <div className="relative flex flex-col items-center text-center max-w-2xl mx-auto">
        <div className="w-16 h-16 border-2 border-[#F59E0B] flex items-center justify-center text-[#F59E0B]">
          <Lock size={28} />
        </div>
        <p className="mt-6 font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">
          // eğitim.üye.erişimi.gerekli
        </p>
        <h2 className="mt-2 font-outfit font-bold text-3xl md:text-4xl text-white tracking-tight">
          Bu Alan Sadece Üyelere Özel
        </h2>
        <p className="mt-4 text-white/70 leading-relaxed text-base md:text-lg">
          Eğitim içeriklerimize yalnızca <strong className="text-white">admin tarafından onaylanmış üyeler</strong> ya da <strong className="text-white">eğitimlere kayıt yaptıran katılımcılar</strong> erişebilir.
        </p>
        <p className="mt-2 text-white/50 text-sm">
          Erişim almak için PrivyAlgo eğitim programlarına kayıt olun veya admin ile iletişime geçin.
        </p>

        {!compact && (
          <div className="mt-8 flex flex-col sm:flex-row items-center gap-3">
            {!user && (
              <button
                onClick={startLogin}
                data-testid="edu-gate-login"
                className="inline-flex items-center gap-2 bg-[#F59E0B] hover:bg-[#D97706] text-black px-5 py-3 font-jetbrains text-[11px] uppercase tracking-widest"
              >
                Google ile Giriş Yap
              </button>
            )}
            <a
              href="https://privyalgo.com"
              target="_blank"
              rel="noreferrer"
              data-testid="edu-gate-register"
              className="inline-flex items-center gap-2 border border-white/20 hover:border-[#F59E0B] hover:text-[#F59E0B] text-white px-5 py-3 font-jetbrains text-[11px] uppercase tracking-widest"
            >
              <Mail size={14} /> Eğitim Kayıt Bilgisi
            </a>
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-white/50 hover:text-white px-5 py-3 font-jetbrains text-[11px] uppercase tracking-widest"
            >
              Anasayfa
            </Link>
          </div>
        )}

        {user && (
          <p className="mt-6 font-jetbrains text-[10px] uppercase tracking-widest text-white/40">
            Giriş yapıldı: <span className="text-white/70">{user.email}</span> · Erişim yok
          </p>
        )}
      </div>
    </div>
  );
};
