import { Lock, MessageCircle } from "lucide-react";
import { Link } from "react-router-dom";

const WHATSAPP_NUMBER = "905415478141";
const WHATSAPP_MSG = encodeURIComponent(
  "Merhaba, PrivyAlgo Blog eğitim içeriklerine erişim talebim var. Paket bilgilerim:"
);

export const EducationGate = () => {
  return (
    <div
      data-testid="education-gate"
      className="relative border border-[#F59E0B]/40 bg-gradient-to-br from-[#F59E0B]/10 via-black to-black p-8 md:p-14 overflow-hidden"
    >
      <div className="absolute top-0 left-0 w-24 h-24 border-l-2 border-t-2 border-[#F59E0B]/60" />
      <div className="absolute bottom-0 right-0 w-24 h-24 border-r-2 border-b-2 border-[#F59E0B]/60" />

      <div className="relative flex flex-col items-center text-center max-w-3xl mx-auto">
        <div className="w-16 h-16 border-2 border-[#F59E0B] flex items-center justify-center text-[#F59E0B]">
          <Lock size={28} />
        </div>
        <p className="mt-6 font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">
          // eğitim.üye.erişimi.gerekli
        </p>
        <h2 className="mt-2 font-outfit font-bold text-2xl md:text-3xl lg:text-4xl text-white tracking-tight leading-tight">
          Bu Alan Sadece PrivyAlgo Terminal Paketini satın almış ve/veya &ldquo;Eğitim İçerikleri&rdquo;ni satın almış kullanıcılara özeldir!
        </h2>
        <p className="mt-6 text-white/75 leading-relaxed text-base md:text-lg">
          Eğitim içeriklerimize erişmek için <strong className="text-white">PrivyAlgo Terminal paketlerimizden</strong> veya <strong className="text-white">Eğitim paketlerimizden</strong> birini satın almış ve <strong className="text-white">üyeliğinizin admin tarafından onaylanmış</strong> olması gerekmektedir. Lütfen paketlerden birine sahip olup olmadığınızı kontrol edin, eğer bu paketlerden herhangi birine sahipseniz{" "}
          <a
            href={`https://wa.me/${WHATSAPP_NUMBER}?text=${WHATSAPP_MSG}`}
            target="_blank"
            rel="noreferrer"
            data-testid="edu-gate-whatsapp-inline"
            className="text-[#10B981] hover:text-[#F59E0B] underline underline-offset-4 font-semibold"
          >
            +90 541 547 8141
          </a>{" "}
          whatsapp destek hattımıza msj atınız!
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center gap-3">
          <a
            href={`https://wa.me/${WHATSAPP_NUMBER}?text=${WHATSAPP_MSG}`}
            target="_blank"
            rel="noreferrer"
            data-testid="edu-gate-whatsapp"
            className="inline-flex items-center gap-2 bg-[#10B981] hover:bg-[#0EA371] text-black px-6 py-3 font-jetbrains text-[11px] uppercase tracking-widest"
          >
            <MessageCircle size={14} /> WhatsApp Destek
          </a>
          <Link
            to="/"
            data-testid="edu-gate-home"
            className="inline-flex items-center gap-2 text-white/50 hover:text-white px-5 py-3 font-jetbrains text-[11px] uppercase tracking-widest"
          >
            Anasayfa
          </Link>
        </div>
      </div>
    </div>
  );
};
