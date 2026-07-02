import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/ArticleCard";
import { Link } from "react-router-dom";
import { ArrowRight, TrendingUp, Zap } from "lucide-react";

export const Home = () => {
  const [featured, setFeatured] = useState([]);
  const [latest, setLatest] = useState([]);
  const [trending, setTrending] = useState([]);
  const [categories, setCategories] = useState([]);
  const [byCategory, setByCategory] = useState({});

  useEffect(() => {
    (async () => {
      const [feat, all, cats] = await Promise.all([
        api.get("/articles", { params: { featured: true, limit: 5 } }),
        api.get("/articles", { params: { limit: 12 } }),
        api.get("/categories"),
      ]);
      const featuredArr = feat.data || [];
      const allArr = all.data || [];
      setFeatured(featuredArr.length ? featuredArr : allArr.slice(0, 3));
      setLatest(allArr);
      setTrending(allArr.slice(0, 5));
      setCategories(cats.data || []);

      // fetch a few per category
      const map = {};
      await Promise.all((cats.data || []).slice(0, 3).map(async (c) => {
        const r = await api.get("/articles", { params: { category: c.slug, limit: 4 } });
        map[c.slug] = { category: c, articles: r.data || [] };
      }));
      setByCategory(map);
    })();
  }, []);

  const hero = featured[0] || latest[0];
  const otherFeatured = featured.slice(1);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Section: Hero + Trending sidebar */}
      <section data-testid="hero-section" className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          {hero ? (
            <ArticleCard article={hero} variant="hero" />
          ) : (
            <EmptyHero />
          )}
        </div>

        <aside className="lg:col-span-4 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h2 className="font-outfit font-bold text-xl text-white inline-flex items-center gap-2">
              <TrendingUp size={18} className="text-[#F59E0B]" /> Trend Makaleler
            </h2>
            <span className="font-jetbrains text-[10px] uppercase tracking-widest text-white/40">Canlı</span>
          </div>
          <div className="flex flex-col gap-3">
            {trending.length === 0 && <p className="text-sm text-white/50">Henüz makale yok.</p>}
            {trending.slice(0, 5).map((a, i) => (
              <div key={a.id} className="flex gap-4 items-start border-b border-white/5 pb-3 last:border-b-0">
                <span className="font-outfit font-black text-4xl text-[#F59E0B]/40 leading-none">{String(i + 1).padStart(2, "0")}</span>
                <Link to={`/makale/${a.slug}`} data-testid={`trending-${a.slug}`} className="flex-1 group">
                  <span className="font-jetbrains text-[10px] uppercase tracking-widest text-[#10B981]">
                    {(a.category_names && a.category_names.length ? a.category_names : [a.category_name]).join(" · ")}
                  </span>
                  <h4 className="font-outfit font-semibold text-white text-sm mt-1 leading-snug group-hover:text-[#F59E0B] transition-colors line-clamp-3">
                    {a.title}
                  </h4>
                </Link>
              </div>
            ))}
          </div>

          <div className="mt-4 border border-[#F59E0B]/30 bg-[#F59E0B]/5 p-5">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-[#F59E0B]" />
              <h4 className="font-outfit font-bold text-white">Terminal&apos;de Görüşürüz</h4>
            </div>
            <p className="mt-2 text-sm text-white/70 leading-relaxed">
              BIST + Wall Street kantitatif analiz platformu. TF AL/SAT sinyalleri, Hedge Wall ve Net GEX bir arada.
            </p>
            <a
              href="https://privyalgo.com"
              target="_blank"
              rel="noreferrer"
              data-testid="cta-privyalgo"
              className="mt-3 inline-flex items-center gap-2 font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B] hover:text-white"
            >
              PrivyAlgo Terminal <ArrowRight size={12} />
            </a>
          </div>
        </aside>
      </section>

      {/* Section: Additional Featured Articles */}
      {otherFeatured.length > 0 && (
        <section className="mt-14" data-testid="featured-section">
          <SectionHeader
            title="Öne Çıkan Makaleler"
            subtitle="Editör seçimi ile PrivyAlgo'nun mercek altına aldığı yazılar"
            eyebrow="featured"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {otherFeatured.map(a => <ArticleCard key={a.id} article={a} />)}
          </div>
        </section>
      )}

      {/* Section: Categories bar */}
      <section className="mt-14 border-y border-white/10 py-4 flex items-center gap-3 overflow-x-auto no-scrollbar" data-testid="category-bar">
        <span className="font-jetbrains text-[10px] uppercase tracking-widest text-white/40 whitespace-nowrap">Kategoriler //</span>
        {categories.map(c => (
          <Link
            key={c.slug}
            to={`/kategori/${c.slug}`}
            data-testid={`cat-chip-${c.slug}`}
            className="px-3 py-1 border border-white/10 hover:border-[#F59E0B] hover:text-[#F59E0B] text-white/70 font-jetbrains text-[10px] uppercase tracking-widest whitespace-nowrap transition-colors"
          >
            {c.name}
          </Link>
        ))}
      </section>

      {/* Section: Latest articles grid */}
      <section className="mt-14" data-testid="latest-section">
        <SectionHeader title="Son Makaleler" subtitle="En yeni analiz ve içgörüler" eyebrow="latest" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {latest.slice(0, 9).map(a => <ArticleCard key={a.id} article={a} />)}
        </div>
        {latest.length === 0 && <EmptyState />}
      </section>

      {/* Sections per category */}
      {Object.values(byCategory).map(({ category, articles }) => (
        articles.length > 0 && (
          <section key={category.slug} className="mt-16" data-testid={`section-${category.slug}`}>
            <SectionHeader
              title={category.name}
              subtitle={category.description}
              right={<Link to={`/kategori/${category.slug}`} className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B] hover:text-white inline-flex items-center gap-2">Tümü <ArrowRight size={12} /></Link>}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {articles.map(a => <ArticleCard key={a.id} article={a} />)}
            </div>
          </section>
        )
      ))}
    </div>
  );
};

const SectionHeader = ({ title, subtitle, right, eyebrow }) => (
  <div className="flex items-end justify-between border-b border-white/10 pb-4 mb-8">
    <div>
      <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// {eyebrow || title}</div>
      <h2 className="font-outfit font-bold text-3xl md:text-4xl text-white mt-1">{title}</h2>
      {subtitle && <p className="mt-1 text-white/50 text-sm">{subtitle}</p>}
    </div>
    {right}
  </div>
);

const EmptyHero = () => (
  <div className="relative border border-white/10 bg-[#0A0A0A] min-h-[500px] flex items-center justify-center overflow-hidden">
    <div
      className="absolute inset-0 bg-cover bg-center opacity-30"
      style={{ backgroundImage: "url(https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1600&q=80)" }}
    />
    <div className="absolute inset-0 bg-gradient-to-t from-black to-transparent" />
    <div className="relative text-center px-6">
      <span className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// waiting for signal</span>
      <h1 className="font-outfit font-bold text-4xl md:text-6xl text-white mt-2">PrivyAlgo Blog</h1>
      <p className="mt-3 text-white/60 max-w-2xl mx-auto">
        BIST · Wall Street · Opsiyonlar · Kripto. Kantitatif finans ve algoritmik ticaret için araştırma ve eğitim yayınları.
      </p>
    </div>
  </div>
);

const EmptyState = () => (
  <div className="border border-dashed border-white/10 p-16 text-center">
    <p className="text-white/50 font-jetbrains text-xs uppercase tracking-widest">no.articles.yet</p>
    <p className="text-white/70 mt-2 font-outfit text-xl">Henüz yayınlanmış makale yok</p>
    <p className="text-white/40 mt-1 text-sm">Giriş yapıp panelden ilk makaleni yayınla.</p>
  </div>
);
