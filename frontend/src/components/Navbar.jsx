import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Search as SearchIcon, LogOut, User, LayoutDashboard, Menu, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [categories, setCategories] = useState([]);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    api.get("/categories").then(r => setCategories(r.data || [])).catch(() => {});
  }, []);

  const onSearch = (e) => {
    e.preventDefault();
    if (q.trim()) navigate(`/arama?q=${encodeURIComponent(q.trim())}`);
  };

  const startLogin = () => {
    navigate("/login");
  };

  return (
    <header
      data-testid="site-navbar"
      className="sticky top-0 z-40 bg-black/85 backdrop-blur-xl border-b border-white/10"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-32">
          <Link to="/" data-testid="nav-logo" className="flex items-center gap-4 group">
            <img
              src="https://customer-assets.emergentagent.com/job_privyalgo-blog/artifacts/b8het9y5_logo-horizontal.png"
              alt="PrivyAlgo"
              // YENİ EKLENEN KISIM: Logoyu yatayda büyütecek ve menüye tam oturtacak sınıflar
              className="w-48 md:w-64 h-auto max-h-28 object-contain group-hover:scale-105 transition-transform"
            />
          </Link>

          <nav className="hidden lg:flex items-center gap-8 font-jetbrains text-[11px] uppercase tracking-widest">
            <Link data-testid="nav-home" to="/" className="text-white/70 hover:text-[#F59E0B] transition-colors">Blog</Link>
            <div className="relative group">
              <button data-testid="nav-categories" className="text-white/70 hover:text-[#F59E0B] transition-colors inline-flex items-center gap-1">
                Kategoriler
              </button>
              <div className="absolute top-full left-0 mt-3 min-w-[220px] bg-[#0A0A0A] border border-white/10 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                {categories.map((c) => (
                  <Link
                    key={c.slug}
                    to={`/kategori/${c.slug}`}
                    data-testid={`nav-cat-${c.slug}`}
                    className="block px-4 py-2.5 text-white/70 hover:text-[#F59E0B] hover:bg-white/5 border-b border-white/5 last:border-b-0"
                  >
                    {c.name}
                  </Link>
                ))}
              </div>
            </div>
            <Link data-testid="nav-education" to="/kategori/egitim" className="text-white/70 hover:text-[#F59E0B] transition-colors">Opsiyon101</Link>
            <a data-testid="nav-external" href="https://privyalgo.com" target="_blank" rel="noreferrer" className="text-white/70 hover:text-[#10B981] transition-colors">Terminaller ↗</a>
          </nav>

          <div className="flex items-center gap-3">
            <form onSubmit={onSearch} className="hidden md:flex items-center border border-white/10 hover:border-white/30 transition-colors">
              <input
                data-testid="search-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ara..."
                className="bg-transparent px-3 py-2 text-sm outline-none text-white placeholder:text-white/40 w-40 font-jetbrains"
              />
              <button data-testid="search-submit" type="submit" className="px-3 py-2 text-white/60 hover:text-[#F59E0B]">
                <SearchIcon size={16} />
              </button>
            </form>

            {user ? (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/dashboard" data-testid="nav-dashboard" className="flex items-center gap-2 px-3 py-2 border border-white/10 hover:border-[#F59E0B] text-white/80 hover:text-[#F59E0B] font-jetbrains text-[11px] uppercase tracking-widest">
                  <LayoutDashboard size={14} /> Panel
                </Link>
                <button
                  onClick={logout}
                  data-testid="nav-logout"
                  className="flex items-center gap-2 px-3 py-2 border border-white/10 hover:border-[#EF4444] text-white/80 hover:text-[#EF4444] font-jetbrains text-[11px] uppercase tracking-widest"
                >
                  <LogOut size={14} /> Çıkış
                </button>
              </div>
            ) : (
              <Button
                onClick={startLogin}
                data-testid="nav-login-btn"
                className="hidden md:inline-flex bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest h-9 px-4"
              >
                Giriş Yap
              </Button>
            )}

            <button
              className="lg:hidden text-white p-2"
              onClick={() => setMobileOpen(!mobileOpen)}
              data-testid="mobile-menu-toggle"
            >
              {mobileOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </div>

      {mobileOpen && (
        <div className="lg:hidden border-t border-white/10 bg-[#050505]" data-testid="mobile-menu">
          <div className="px-4 py-4 space-y-3">
            <form onSubmit={onSearch} className="flex items-center border border-white/10">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ara..."
                className="flex-1 bg-transparent px-3 py-2 text-sm outline-none text-white placeholder:text-white/40 font-jetbrains"
              />
              <button type="submit" className="px-3 py-2 text-[#F59E0B]"><SearchIcon size={16} /></button>
            </form>
            <Link onClick={() => setMobileOpen(false)} to="/" className="block py-2 text-white/80">Anasayfa</Link>
            {categories.map(c => (
              <Link key={c.slug} onClick={() => setMobileOpen(false)} to={`/kategori/${c.slug}`} className="block py-2 text-white/70">
                {c.name}
              </Link>
            ))}
            {user ? (
              <>
                <Link onClick={() => setMobileOpen(false)} to="/dashboard" className="block py-2 text-[#F59E0B]">Panel</Link>
                <button onClick={() => { logout(); setMobileOpen(false); }} className="block py-2 text-[#EF4444]">Çıkış</button>
              </>
            ) : (
              <button onClick={startLogin} className="w-full py-2 bg-[#F59E0B] text-black font-bold">Giriş Yap</button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
