import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export const Footer = () => {
  const [categories, setCategories] = useState([]);
  useEffect(() => { api.get("/categories").then(r => setCategories(r.data || [])); }, []);

  return (
    <footer className="mt-24 border-t border-white/10 bg-[#050505]" data-testid="site-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 grid grid-cols-1 md:grid-cols-4 gap-10">
        <div className="md:col-span-2">
          <div className="flex items-center gap-4">
            <img
              src="https://customer-assets.emergentagent.com/job_privyalgo-blog/artifacts/b8het9y5_logo-horizontal.png"
              alt="PrivyAlgo"
              className="h-36 w-36 object-contain"
            />
            <div>
              <div className="font-outfit font-bold text-2xl text-white">PrivyAlgo Blog</div>
              <div className="font-jetbrains text-[10px] text-white/40 uppercase tracking-widest mt-1">nFinans · Kantitatif Araştırma</div>
            </div>
          </div>
          <p className="mt-4 text-sm text-white/60 leading-relaxed max-w-md">
            Borsa İstanbul, Wall Street ve türev piyasaları için algoritmik analiz, sinyal ve eğitim içerikleri. Veriye dayalı yatırım felsefesinin haber ve yayın merkezi.
          </p>
        </div>

        <div>
          <h4 className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Kategoriler</h4>
          <ul className="mt-4 space-y-2 text-sm">
            {categories.map(c => (
              <li key={c.slug}>
                <Link to={`/kategori/${c.slug}`} className="text-white/70 hover:text-white transition-colors">
                  {c.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Bağlantılar</h4>
          <ul className="mt-4 space-y-2 text-sm">
            <li><a href="https://privyalgo.com" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#10B981]">PrivyAlgo Terminal ↗</a></li>
            <li><a href="https://bist.privyalgo.com" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#10B981]">BIST Terminal ↗</a></li>
            <li><a href="https://wallstreet.privyalgo.com" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#10B981]">Wall Street Terminal ↗</a></li>
            <li><a href="https://www.youtube.com/@NFinans" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#10B981]">YouTube @NFinans ↗</a></li>
          </ul>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="font-jetbrains text-[10px] uppercase tracking-widest text-white/40">
            © {new Date().getFullYear()} PrivyAlgo Blog · nFinans Araştırma
          </p>
          <p className="font-jetbrains text-[10px] uppercase tracking-widest text-white/40">
            Piyasa · Veri · Algoritma
          </p>
        </div>
      </div>
    </footer>
  );
};
