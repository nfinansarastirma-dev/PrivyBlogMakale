import { Link } from "react-router-dom";
import { resolveImage } from "@/lib/api";
import { Clock, Eye } from "lucide-react";

const fallback = "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&q=80";

export const ArticleCard = ({ article, variant = "grid" }) => {
  const img = resolveImage(article.cover_image) || fallback;
  const date = article.published_at ? new Date(article.published_at).toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" }) : "";

  if (variant === "hero") {
    return (
      <Link
        to={`/makale/${article.slug}`}
        data-testid={`article-hero-${article.slug}`}
        className="relative block group overflow-hidden border border-white/10 bg-[#0A0A0A] min-h-[500px] lg:min-h-[560px]"
      >
        <div
          className="absolute inset-0 bg-cover bg-center opacity-70 group-hover:opacity-90 group-hover:scale-105 transition-all duration-700"
          style={{ backgroundImage: `url(${img})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/70 to-transparent" />
        <div className="relative z-10 flex flex-col justify-end h-full p-6 md:p-10">
          <div className="inline-flex items-center gap-2 font-jetbrains text-[10px] uppercase tracking-widest">
            <span className="bg-[#10B981] text-black px-2 py-1">Öne Çıkan</span>
            <span className="border border-white/20 px-2 py-1 text-white/90">{article.category_name}</span>
          </div>
          <h1 className="font-outfit font-bold text-3xl md:text-5xl leading-[1.05] mt-4 text-white group-hover:text-[#10B981] transition-colors max-w-3xl">
            {article.title}
          </h1>
          {article.excerpt && (
            <p className="mt-3 text-white/70 max-w-2xl text-base md:text-lg leading-relaxed line-clamp-2">{article.excerpt}</p>
          )}
          <div className="mt-5 flex items-center gap-4 font-jetbrains text-[11px] uppercase tracking-widest text-white/50">
            <span>{article.author_name}</span>
            <span>·</span>
            <span>{date}</span>
            <span>·</span>
            <span className="inline-flex items-center gap-1"><Clock size={12} /> {article.reading_minutes} dk</span>
          </div>
        </div>
      </Link>
    );
  }

  if (variant === "list") {
    return (
      <Link
        to={`/makale/${article.slug}`}
        data-testid={`article-list-${article.slug}`}
        className="flex gap-4 border border-white/10 bg-[#0A0A0A] hover:border-white/30 p-3 group transition-colors"
      >
        <div className="w-24 h-24 flex-shrink-0 bg-cover bg-center border border-white/10" style={{ backgroundImage: `url(${img})` }} />
        <div className="flex-1 min-w-0">
          <span className="font-jetbrains text-[10px] uppercase tracking-widest text-[#10B981]">{article.category_name}</span>
          <h3 className="font-outfit font-semibold text-white text-sm md:text-base mt-1 leading-snug line-clamp-3 group-hover:text-[#10B981] transition-colors">
            {article.title}
          </h3>
          <p className="mt-1 font-jetbrains text-[10px] uppercase tracking-widest text-white/40">{date}</p>
        </div>
      </Link>
    );
  }

  return (
    <Link
      to={`/makale/${article.slug}`}
      data-testid={`article-card-${article.slug}`}
      className="flex flex-col border border-white/10 bg-[#0A0A0A] hover:border-white/30 group transition-colors"
    >
      <div className="aspect-[16/10] bg-cover bg-center border-b border-white/10" style={{ backgroundImage: `url(${img})` }} />
      <div className="p-5 flex-1 flex flex-col">
        <div className="flex items-center gap-3 font-jetbrains text-[10px] uppercase tracking-widest">
          <span className="text-[#10B981]">{article.category_name}</span>
          <span className="text-white/30">·</span>
          <span className="text-white/50">{date}</span>
        </div>
        <h3 className="font-outfit font-bold text-xl text-white mt-3 leading-tight group-hover:text-[#10B981] transition-colors line-clamp-2">
          {article.title}
        </h3>
        {article.excerpt && (
          <p className="mt-2 text-sm text-white/60 line-clamp-2 leading-relaxed">{article.excerpt}</p>
        )}
        <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between font-jetbrains text-[10px] uppercase tracking-widest text-white/40">
          <span>{article.author_name}</span>
          <span className="inline-flex items-center gap-3">
            <span className="inline-flex items-center gap-1"><Clock size={11} /> {article.reading_minutes}dk</span>
            <span className="inline-flex items-center gap-1"><Eye size={11} /> {article.views || 0}</span>
          </span>
        </div>
      </div>
    </Link>
  );
};
