import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, resolveImage } from "@/lib/api";
import { Clock, Eye, Calendar, ArrowLeft, Tag } from "lucide-react";
import { ArticleCard } from "@/components/ArticleCard";

export const Article = () => {
  const { slug } = useParams();
  const [article, setArticle] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const [a, rel] = await Promise.all([
          api.get(`/articles/${slug}`),
          api.get(`/articles/${slug}/related`),
        ]);
        setArticle(a.data);
        setRelated(rel.data || []);
      } catch (e) {
        setError("Makale bulunamadı");
      } finally {
        setLoading(false);
      }
    })();
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-24 text-center">
        <p className="font-jetbrains text-xs uppercase tracking-widest text-white/50">loading...</p>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-24 text-center">
        <p className="font-outfit text-3xl text-white">Makale bulunamadı</p>
        <Link to="/" className="mt-4 inline-flex items-center gap-2 text-[#F59E0B] hover:text-white font-jetbrains text-xs uppercase tracking-widest">
          <ArrowLeft size={14} /> Ana sayfaya dön
        </Link>
      </div>
    );
  }

  const date = article.published_at ? new Date(article.published_at).toLocaleDateString("tr-TR", { day: "2-digit", month: "long", year: "numeric" }) : "";
  const cover = resolveImage(article.cover_image);

  return (
    <article className="pb-16" data-testid="article-page">
      {/* Hero */}
      <div className="relative border-b border-white/10 overflow-hidden">
        {cover && (
          <>
            <div className="absolute inset-0 bg-cover bg-center opacity-40" style={{ backgroundImage: `url(${cover})` }} />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/60 to-black" />
          </>
        )}
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-14 md:py-20">
          <div className="flex flex-wrap gap-2" data-testid="article-category-badges">
            {(article.category_slugs && article.category_slugs.length
              ? article.category_slugs.map((s, i) => ({ slug: s, name: article.category_names?.[i] || s }))
              : [{ slug: article.category_slug, name: article.category_name }]
            ).map(c => (
              <Link
                key={c.slug}
                to={`/kategori/${c.slug}`}
                className="inline-block bg-[#F59E0B] text-black px-3 py-1 font-jetbrains text-[10px] uppercase tracking-widest hover:bg-[#10B981]"
              >
                {c.name}
              </Link>
            ))}
          </div>
          <h1 data-testid="article-title" className="font-outfit font-bold text-4xl md:text-6xl leading-[1.05] mt-6 text-white tracking-tight">
            {article.title}
          </h1>
          {article.excerpt && (
            <p className="mt-5 text-lg md:text-xl text-white/70 leading-relaxed max-w-3xl">{article.excerpt}</p>
          )}
          <div className="mt-8 flex flex-wrap items-center gap-4 text-white/50 font-jetbrains text-[11px] uppercase tracking-widest">
            <span className="text-white/80">{article.author_name}</span>
            <span>·</span>
            <span className="inline-flex items-center gap-1"><Calendar size={12} /> {date}</span>
            <span>·</span>
            <span className="inline-flex items-center gap-1"><Clock size={12} /> {article.reading_minutes} dk okuma</span>
            <span>·</span>
            <span className="inline-flex items-center gap-1"><Eye size={12} /> {article.views} görüntüleme</span>
          </div>
        </div>
      </div>

      {cover && (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10">
          <img src={cover} alt={article.title} className="w-full max-h-[520px] object-cover border border-white/10" />
        </div>
      )}

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
        <div
          data-testid="article-content"
          className="article-content"
          dangerouslySetInnerHTML={{ __html: article.content_html || "<p><em>İçerik yakında...</em></p>" }}
        />

        {article.tags?.length > 0 && (
          <div className="mt-10 pt-6 border-t border-white/10 flex flex-wrap items-center gap-2">
            <Tag size={14} className="text-[#F59E0B]" />
            {article.tags.map(t => (
              <Link
                key={t}
                to={`/arama?q=${encodeURIComponent(t)}`}
                className="font-jetbrains text-[10px] uppercase tracking-widest border border-white/10 px-2 py-1 text-white/70 hover:border-[#F59E0B] hover:text-[#F59E0B]"
              >
                #{t}
              </Link>
            ))}
          </div>
        )}

        {/* Author box */}
        <div className="mt-10 border border-white/10 bg-[#0A0A0A] p-6 flex items-center gap-4">
          {article.author_picture ? (
            <img src={article.author_picture} alt="" className="w-14 h-14 border border-white/10 object-cover" />
          ) : (
            <div className="w-14 h-14 border border-[#F59E0B] flex items-center justify-center font-jetbrains text-[#F59E0B] font-bold text-xl">
              {article.author_name?.[0]?.toUpperCase() || "?"}
            </div>
          )}
          <div>
            <p className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Yazar</p>
            <p className="font-outfit font-bold text-white text-lg">{article.author_name}</p>
          </div>
        </div>
      </div>

      {related.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
          <div className="border-b border-white/10 pb-3 mb-8">
            <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// related</div>
            <h2 className="font-outfit font-bold text-2xl md:text-3xl text-white mt-1">İlgili Makaleler</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {related.map(a => <ArticleCard key={a.id} article={a} />)}
          </div>
        </section>
      )}
    </article>
  );
};
