import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/ArticleCard";

export const Category = () => {
  const { slug } = useParams();
  const [articles, setArticles] = useState([]);
  const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get("/articles", { params: { category: slug, limit: 60 } }),
      api.get("/categories"),
    ]).then(([a, c]) => {
      setArticles(a.data || []);
      setCategory((c.data || []).find(x => x.slug === slug) || { name: slug, description: "" });
    }).finally(() => setLoading(false));
  }, [slug]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10" data-testid="category-page">
      <div className="border-b border-white/10 pb-8 mb-10">
        <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// category</div>
        <h1 className="font-outfit font-bold text-5xl md:text-6xl text-white mt-2 tracking-tight">{category?.name}</h1>
        {category?.description && <p className="mt-3 text-white/60 max-w-3xl text-lg">{category.description}</p>}
        <p className="mt-3 font-jetbrains text-[11px] uppercase tracking-widest text-white/40">{articles.length} makale bulundu</p>
      </div>

      {loading ? (
        <p className="text-white/50 font-jetbrains text-xs uppercase tracking-widest">loading...</p>
      ) : articles.length === 0 ? (
        <div className="border border-dashed border-white/10 p-16 text-center">
          <p className="text-white/50 font-jetbrains text-xs uppercase tracking-widest">no.articles.here.yet</p>
          <p className="text-white/70 mt-2 font-outfit text-xl">Bu kategoride henüz makale yok</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map(a => <ArticleCard key={a.id} article={a} />)}
        </div>
      )}
    </div>
  );
};
