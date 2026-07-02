import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, resolveImage } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { RichEditor } from "@/components/RichEditor";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ImageIcon, Save, Send, X, Plus, Check } from "lucide-react";
import { toast } from "sonner";

export const ArticleEditor = () => {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const { user, loading } = useAuth();
  const [categories, setCategories] = useState([]);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [newCatName, setNewCatName] = useState("");
  const [addingCat, setAddingCat] = useState(false);
  const coverRef = useRef(null);

  const [form, setForm] = useState({
    title: "",
    excerpt: "",
    content_html: "",
    cover_image: "",
    category_slugs: [],
    tags: "",
    status: "draft",
    featured: false,
  });

  useEffect(() => {
    if (!loading && !user) navigate("/", { replace: true });
  }, [user, loading, navigate]);

  const loadCategories = () => api.get("/categories").then(r => setCategories(r.data || []));

  useEffect(() => {
    loadCategories();
    if (isEdit) {
      api.get(`/my/articles/${id}`).then(r => {
        const a = r.data;
        setForm({
          title: a.title,
          excerpt: a.excerpt || "",
          content_html: a.content_html || "",
          cover_image: a.cover_image || "",
          category_slugs: (a.category_slugs && a.category_slugs.length ? a.category_slugs : (a.category_slug ? [a.category_slug] : [])),
          tags: (a.tags || []).join(", "),
          status: a.status,
        });
      });
    }
  }, [id, isEdit]);

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const uploadCover = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post("/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      set("cover_image", data.url);
      toast.success("Kapak yüklendi");
    } catch {
      toast.error("Yükleme hatası");
    } finally {
      setUploading(false);
    }
  };

  const save = async (publish = false) => {
    if (!form.title.trim()) { toast.error("Başlık gerekli"); return; }
    if (!form.category_slugs || form.category_slugs.length === 0) { toast.error("En az bir kategori seç"); return; }
    setSaving(true);
    try {
      const payload = {
        title: form.title.trim(),
        excerpt: form.excerpt,
        content_html: form.content_html,
        cover_image: form.cover_image,
        category_slugs: form.category_slugs,
        tags: form.tags.split(",").map(t => t.trim()).filter(Boolean),
        status: publish ? "published" : form.status,
      };
      if (user.role === "admin") {
        payload.featured = !!form.featured;
      }
      if (isEdit) {
        await api.patch(`/articles/${id}`, payload);
      } else {
        const { data } = await api.post("/articles", payload);
        if (publish && data?.slug) {
          toast.success("Yayınlandı");
          navigate(`/makale/${data.slug}`);
          return;
        }
      }
      toast.success(publish ? "Yayınlandı" : "Kaydedildi");
      navigate("/dashboard");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Kayıt hatası");
    } finally {
      setSaving(false);
    }
  };

  const toggleCategory = (slug) => {
    setForm(prev => {
      const has = prev.category_slugs.includes(slug);
      return { ...prev, category_slugs: has ? prev.category_slugs.filter(s => s !== slug) : [...prev.category_slugs, slug] };
    });
  };

  const addCategory = async (e) => {
    e.preventDefault();
    if (!newCatName.trim()) return;
    setAddingCat(true);
    try {
      const { data } = await api.post("/admin/categories", { name: newCatName.trim() });
      toast.success("Kategori eklendi");
      setNewCatName("");
      await loadCategories();
      // auto-select the new one
      setForm(prev => ({ ...prev, category_slugs: [...prev.category_slugs, data.slug] }));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Eklenemedi");
    } finally {
      setAddingCat(false);
    }
  };

  if (loading || !user) {
    return <div className="max-w-7xl mx-auto px-4 py-20 text-center font-jetbrains text-white/60">yükleniyor...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="article-editor">
      <button onClick={() => navigate("/dashboard")} className="inline-flex items-center gap-2 font-jetbrains text-[11px] uppercase tracking-widest text-white/60 hover:text-[#F59E0B]">
        <ArrowLeft size={14} /> Panele Dön
      </button>

      <div className="mt-4 flex items-end justify-between border-b border-white/10 pb-6">
        <div>
          <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// {isEdit ? "editor.update" : "editor.new"}</div>
          <h1 className="font-outfit font-bold text-3xl md:text-4xl text-white mt-1">{isEdit ? "Makaleyi Düzenle" : "Yeni Makale"}</h1>
        </div>
        <div className="flex gap-2">
          <Button
            data-testid="save-draft-btn"
            onClick={() => save(false)}
            disabled={saving}
            className="rounded-none bg-transparent border border-white/20 hover:border-white text-white font-jetbrains text-[11px] uppercase tracking-widest h-10 px-4"
          >
            <Save size={14} className="mr-2" /> Taslak Kaydet
          </Button>
          {user.role === "admin" && (
            <Button
              data-testid="publish-btn"
              onClick={() => save(true)}
              disabled={saving}
              className="rounded-none bg-[#F59E0B] hover:bg-[#D97706] text-black font-jetbrains text-[11px] uppercase tracking-widest h-10 px-4"
            >
              <Send size={14} className="mr-2" /> Yayınla
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-8">
        <div className="lg:col-span-8 space-y-4">
          <input
            data-testid="editor-title"
            value={form.title}
            onChange={(e) => set("title", e.target.value)}
            placeholder="Makale başlığı..."
            className="w-full bg-transparent text-3xl md:text-4xl font-outfit font-bold text-white outline-none border-b border-white/10 focus:border-[#F59E0B] pb-3 placeholder:text-white/20"
          />
          <textarea
            data-testid="editor-excerpt"
            value={form.excerpt}
            onChange={(e) => set("excerpt", e.target.value)}
            placeholder="Kısa özet (isteğe bağlı)..."
            rows={2}
            className="w-full bg-transparent text-white/80 outline-none border-b border-white/10 focus:border-[#F59E0B] pb-3 placeholder:text-white/30 font-ibm-plex"
          />

          <RichEditor
            value={form.content_html}
            onChange={(html) => set("content_html", html)}
          />
        </div>

        <aside className="lg:col-span-4 space-y-4">
          <div className="border border-white/10 p-4">
            <h4 className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B] mb-3">Kapak Görseli</h4>
            {form.cover_image ? (
              <div className="relative">
                <img src={resolveImage(form.cover_image)} alt="" className="w-full aspect-video object-cover border border-white/10" />
                <button
                  onClick={() => set("cover_image", "")}
                  data-testid="remove-cover"
                  className="absolute top-2 right-2 p-1.5 bg-black/80 border border-white/20 hover:border-[#EF4444] text-white hover:text-[#EF4444]"
                ><X size={12} /></button>
              </div>
            ) : (
              <button
                onClick={() => coverRef.current?.click()}
                data-testid="upload-cover"
                className="w-full aspect-video border border-dashed border-white/20 hover:border-[#F59E0B] flex flex-col items-center justify-center gap-2 text-white/40 hover:text-[#F59E0B] transition-colors"
              >
                <ImageIcon size={28} />
                <span className="font-jetbrains text-[10px] uppercase tracking-widest">{uploading ? "yükleniyor..." : "kapak yükle"}</span>
              </button>
            )}
            <input
              ref={coverRef}
              type="file"
              accept="image/*"
              className="hidden"
              data-testid="cover-input"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadCover(f); e.target.value = ""; }}
            />
          </div>

          <div className="border border-white/10 p-4 space-y-3">
            <div>
              <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Kategoriler <span className="text-white/40 normal-case">(çoklu seçim)</span></label>
              <div className="mt-2 max-h-56 overflow-y-auto border border-white/10 bg-black" data-testid="editor-category-list">
                {categories.length === 0 && <p className="p-3 text-white/40 text-xs font-jetbrains">yükleniyor...</p>}
                {categories.map(c => {
                  const checked = form.category_slugs.includes(c.slug);
                  return (
                    <label
                      key={c.slug}
                      data-testid={`cat-opt-${c.slug}`}
                      className={`flex items-center gap-2 px-3 py-2 cursor-pointer border-b border-white/5 last:border-b-0 font-jetbrains text-xs uppercase tracking-wider transition-colors ${checked ? "bg-[#F59E0B]/10 text-[#F59E0B]" : "text-white/70 hover:bg-white/5"}`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleCategory(c.slug)}
                        className="accent-[#F59E0B]"
                      />
                      <span className="flex-1">{c.name}</span>
                      {checked && form.category_slugs[0] === c.slug && (
                        <span className="text-[9px] bg-[#F59E0B] text-black px-1.5 py-0.5">birincil</span>
                      )}
                    </label>
                  );
                })}
              </div>
              {form.category_slugs.length > 0 && (
                <p className="mt-2 font-jetbrains text-[9px] uppercase tracking-widest text-white/40">
                  {form.category_slugs.length} kategori seçili · ilk seçilen birincil kategoridir
                </p>
              )}
              {user.role === "admin" && (
                <form onSubmit={addCategory} className="mt-3 flex gap-1" data-testid="inline-new-cat-form">
                  <input
                    data-testid="inline-new-cat-name"
                    value={newCatName}
                    onChange={(e) => setNewCatName(e.target.value)}
                    placeholder="+ Yeni kategori"
                    className="flex-1 bg-black border border-white/10 px-2 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-xs text-white placeholder:text-white/30"
                  />
                  <button
                    type="submit"
                    disabled={addingCat}
                    data-testid="inline-new-cat-submit"
                    className="px-3 py-2 border border-[#F59E0B] text-[#F59E0B] hover:bg-[#F59E0B] hover:text-black font-jetbrains text-[10px] uppercase tracking-widest disabled:opacity-40"
                  >
                    <Plus size={14} />
                  </button>
                </form>
              )}
            </div>
            <div>
              <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Etiketler</label>
              <input
                data-testid="editor-tags"
                value={form.tags}
                onChange={(e) => set("tags", e.target.value)}
                placeholder="virgülle ayır, örn: GEX, opsiyon"
                className="mt-2 w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white placeholder:text-white/30"
              />
            </div>
            <div>
              <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Durum</label>
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => set("status", "draft")}
                  data-testid="status-draft"
                  className={`flex-1 px-3 py-2 font-jetbrains text-[10px] uppercase tracking-widest ${form.status === "draft" ? "bg-white text-black" : "border border-white/10 text-white/70"}`}
                >Taslak</button>
                {user.role === "admin" && (
                  <button
                    onClick={() => set("status", "published")}
                    data-testid="status-published"
                    className={`flex-1 px-3 py-2 font-jetbrains text-[10px] uppercase tracking-widest ${form.status === "published" ? "bg-[#F59E0B] text-black" : "border border-white/10 text-white/70"}`}
                  >Yayın</button>
                )}
              </div>
              {user.role !== "admin" && (
                <p className="mt-2 font-jetbrains text-[9px] uppercase tracking-widest text-white/40">
                  Sadece admin yayınlayabilir. Taslak olarak kaydedilir.
                </p>
              )}
            </div>

            {user.role === "admin" && (
              <div className="pt-2 border-t border-white/10">
                <label className="flex items-center gap-3 cursor-pointer group" data-testid="editor-featured-toggle">
                  <input
                    type="checkbox"
                    checked={!!form.featured}
                    onChange={(e) => set("featured", e.target.checked)}
                    className="accent-[#F59E0B] w-4 h-4"
                    data-testid="editor-featured-input"
                  />
                  <div className="flex-1">
                    <p className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B] group-hover:text-white transition-colors">
                      ★ Öne Çıkar
                    </p>
                    <p className="font-jetbrains text-[9px] uppercase tracking-widest text-white/40">
                      Ana sayfa hero/featured bölümünde görünür
                    </p>
                  </div>
                </label>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
