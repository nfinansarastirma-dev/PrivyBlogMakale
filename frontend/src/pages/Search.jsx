import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/ArticleCard";
import { Search as SearchIcon } from "lucide-react";

export const Search = () => {
  const [params, setParams] = useSearchParams();
  const initialQ = params.get("q") || "";
  const [q, setQ] = useState(initialQ);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!initialQ) { setArticles([]); return; }
    setLoading(true);
    api.get("/articles", { params: { q: initialQ, limit: 60 } })
      .then(r => setArticles(r.data || []))
      .finally(() => setLoading(false));
  }, [initialQ]);

  const submit = (e) => {
    e.preventDefault();
    setParams({ q });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10" data-testid="search-page">
      <div className="border-b border-white/10 pb-8 mb-10">
        <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#10B981]">// search</div>
        <h1 className="font-outfit font-bold text-4xl md:text-5xl text-white mt-2">Arama</h1>
        <form onSubmit={submit} className="mt-6 flex items-center border border-white/10 focus-within:border-[#10B981] max-w-2xl">
          <SearchIcon size={16} className="ml-3 text-white/50" />
          <input
            data-testid="search-page-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Anahtar kelime..."
            className="flex-1 bg-transparent px-3 py-3 outline-none text-white placeholder:text-white/40 font-jetbrains text-sm"
          />
          <button data-testid="search-page-submit" type="submit" className="px-5 py-3 bg-[#10B981] text-black font-jetbrains text-[11px] uppercase tracking-widest hover:bg-[#F59E0B]">
            Ara
          </button>
        </form>
      </div>

      {initialQ && (
        <p className="mb-6 font-jetbrains text-[11px] uppercase tracking-widest text-white/50">
          &ldquo;{initialQ}&rdquo; için {articles.length} sonuç
        </p>
      )}

      {loading ? (
        <p className="text-white/50 font-jetbrains text-xs uppercase tracking-widest">loading...</p>
      ) : articles.length === 0 && initialQ ? (
        <div className="border border-dashed border-white/10 p-16 text-center">
          <p className="text-white/70 font-outfit text-xl">Sonuç bulunamadı</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map(a => <ArticleCard key={a.id} article={a} />)}
        </div>
      )}
    </div>
  );
};
