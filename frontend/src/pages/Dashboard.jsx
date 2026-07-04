import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api, resolveImage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { PlusCircle, FileText, Star, Trash2, Edit3, Users, FolderPlus, Shield, PencilRuler, GraduationCap, Check, X, KeyRound, Save } from "lucide-react";
import { toast } from "sonner";

export const Dashboard = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("articles");

  useEffect(() => {
    if (!loading && !user) navigate("/", { replace: true });
  }, [user, loading, navigate]);

  if (loading || !user) {
    return <div className="max-w-7xl mx-auto px-4 py-20 text-center font-jetbrains text-white/60">yükleniyor...</div>;
  }

  const isAdmin = user.role === "admin";

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10" data-testid="dashboard">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <div className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">// {isAdmin ? "admin.console" : "user.console"}</div>
          <h1 className="font-outfit font-bold text-4xl md:text-5xl text-white mt-2">Yönetim Paneli</h1>
          <div className="mt-3 flex items-center gap-3">
            {user.picture ? (
              <img src={user.picture} alt="" className="w-9 h-9 border border-white/10 object-cover" />
            ) : (
              <div className="w-9 h-9 bg-[#F59E0B] text-black flex items-center justify-center font-jetbrains font-bold">{user.name?.[0]?.toUpperCase()}</div>
            )}
            <div>
              <p className="text-white text-sm font-outfit font-semibold">{user.name}</p>
              <p className="font-jetbrains text-[10px] uppercase tracking-widest text-white/50">
                {isAdmin ? <span className="text-[#10B981]">admin</span> : "user"} · {user.email}
              </p>
            </div>
          </div>
        </div>
        <Link
          to="/dashboard/new"
          data-testid="new-article-btn"
          className="inline-flex items-center gap-2 bg-[#F59E0B] hover:bg-[#D97706] text-black px-5 py-3 font-jetbrains text-[11px] uppercase tracking-widest"
        >
          <PlusCircle size={16} /> Yeni Makale
        </Link>
      </div>

      <div className="flex flex-wrap gap-2 mt-6 border-b border-white/10">
        <TabBtn active={tab === "articles"} onClick={() => setTab("articles")} icon={<FileText size={14} />} tid="tab-articles">Makaleler</TabBtn>
        {isAdmin && <TabBtn active={tab === "users"} onClick={() => setTab("users")} icon={<Users size={14} />} tid="tab-users">Kullanıcılar</TabBtn>}
        {isAdmin && <TabBtn active={tab === "categories"} onClick={() => setTab("categories")} icon={<FolderPlus size={14} />} tid="tab-categories">Kategoriler</TabBtn>}
      </div>

      <div className="mt-8">
        {tab === "articles" && <ArticlesTab isAdmin={isAdmin} userId={user.user_id} />}
        {tab === "users" && isAdmin && <UsersTab />}
        {tab === "categories" && isAdmin && <CategoriesTab />}
      </div>
    </div>
  );
};

const TabBtn = ({ active, onClick, children, icon, tid }) => (
  <button
    onClick={onClick}
    data-testid={tid}
    className={`inline-flex items-center gap-2 px-4 py-3 font-jetbrains text-[11px] uppercase tracking-widest border-b-2 -mb-px transition-colors ${
      active ? "border-[#F59E0B] text-[#F59E0B]" : "border-transparent text-white/50 hover:text-white"
    }`}
  >
    {icon}{children}
  </button>
);

const ArticlesTab = ({ isAdmin }) => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const load = () => {
    setLoading(true);
    api.get("/my/articles").then(r => setArticles(r.data || [])).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const del = async (id) => {
    if (!window.confirm("Makale silinsin mi?")) return;
    await api.delete(`/articles/${id}`);
    toast.success("Silindi");
    load();
  };
  const publish = async (a) => {
    const status = a.status === "published" ? "draft" : "published";
    await api.patch(`/articles/${a.id}`, { status });
    toast.success(status === "published" ? "Yayınlandı" : "Taslak yapıldı");
    load();
  };
  const feature = async (a) => {
    await api.patch(`/articles/${a.id}`, { featured: !a.featured });
    toast.success(a.featured ? "Öne çıkarma kaldırıldı" : "Öne çıkarıldı");
    load();
  };

  return (
    <div>
      {loading ? (
        <p className="text-white/50 font-jetbrains text-xs uppercase tracking-widest">yükleniyor...</p>
      ) : articles.length === 0 ? (
        <div className="border border-dashed border-white/10 p-16 text-center">
          <PencilRuler size={32} className="mx-auto text-white/30" />
          <p className="text-white/70 mt-3 font-outfit text-xl">Henüz makale yok</p>
          <p className="text-white/40 mt-1 text-sm">Yukarıdaki &ldquo;Yeni Makale&rdquo; ile başla.</p>
        </div>
      ) : (
        <div className="border border-white/10">
          <div className="hidden md:grid grid-cols-12 gap-4 px-4 py-3 border-b border-white/10 bg-black/60 font-jetbrains text-[10px] uppercase tracking-widest text-white/50">
            <div className="col-span-5">Başlık</div>
            <div className="col-span-2">Kategori</div>
            <div className="col-span-1">Durum</div>
            <div className="col-span-2">Yazar</div>
            <div className="col-span-2 text-right">İşlem</div>
          </div>
          {articles.map(a => (
            <div key={a.id} data-testid={`admin-row-${a.id}`} className="grid grid-cols-1 md:grid-cols-12 gap-3 md:gap-4 px-4 py-4 border-b border-white/5 last:border-b-0 items-center hover:bg-white/[0.02]">
              <div className="col-span-5">
                <div className="flex items-center gap-3">
                  {a.cover_image ? (
                    <img src={resolveImage(a.cover_image)} alt="" className="w-14 h-14 object-cover border border-white/10" />
                  ) : (
                    <div className="w-14 h-14 border border-white/10 bg-black flex items-center justify-center font-jetbrains text-white/30 text-[10px]">no img</div>
                  )}
                  <div className="min-w-0">
                    <p className="font-outfit font-semibold text-white truncate">{a.title}</p>
                    <p className="font-jetbrains text-[10px] uppercase tracking-widest text-white/40">
                      {new Date(a.created_at).toLocaleDateString("tr-TR")} · {a.reading_minutes}dk
                      {a.featured && <span className="ml-2 text-[#10B981]">★ öne çıkan</span>}
                    </p>
                  </div>
                </div>
              </div>
              <div className="col-span-2 font-jetbrains text-[11px] text-[#F59E0B] truncate">
                {(a.category_names && a.category_names.length ? a.category_names : [a.category_name]).join(" · ")}
              </div>
              <div className="col-span-1">
                <span className={`inline-block px-2 py-0.5 font-jetbrains text-[10px] uppercase tracking-widest ${a.status === "published" ? "bg-[#F59E0B] text-black" : "border border-white/20 text-white/70"}`}>
                  {a.status === "published" ? "yayın" : "taslak"}
                </span>
              </div>
              <div className="col-span-2 text-white/60 text-sm truncate">{a.author_name}</div>
              <div className="col-span-2 flex md:justify-end gap-2 flex-wrap">
                <Link to={`/dashboard/edit/${a.id}`} data-testid={`edit-${a.id}`} className="p-2 border border-white/10 hover:border-[#F59E0B] text-white/70 hover:text-[#F59E0B]"><Edit3 size={14} /></Link>
                {isAdmin && (
                  <button data-testid={`publish-${a.id}`} onClick={() => publish(a)} className="p-2 border border-white/10 hover:border-[#10B981] text-white/70 hover:text-[#10B981]" title={a.status === "published" ? "Taslağa al" : "Yayınla"}>
                    <FileText size={14} />
                  </button>
                )}
                {isAdmin && (
                  <button data-testid={`feature-${a.id}`} onClick={() => feature(a)} className={`p-2 border border-white/10 hover:border-[#10B981] ${a.featured ? "text-[#10B981]" : "text-white/70 hover:text-[#10B981]"}`} title="Öne çıkar">
                    <Star size={14} />
                  </button>
                )}
                <button data-testid={`delete-${a.id}`} onClick={() => del(a.id)} className="p-2 border border-white/10 hover:border-[#EF4444] text-white/70 hover:text-[#EF4444]"><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const UsersTab = () => {
  const [users, setUsers] = useState([]);
  const load = () => api.get("/admin/users").then(r => setUsers(r.data || []));
  useEffect(() => { load(); }, []);
  const changeRole = async (u, role) => {
    await api.patch(`/admin/users/${u.user_id}/role`, null, { params: { role } });
    toast.success("Rol güncellendi");
    load();
  };
  const toggleEdu = async (u) => {
    await api.patch(`/admin/users/${u.user_id}/education`, null, { params: { enabled: !u.education_access } });
    toast.success(u.education_access ? "Eğitim erişimi kaldırıldı" : "Eğitim erişimi verildi");
    load();
  };

  return (
    <div className="border border-white/10">
      <div className="hidden md:grid grid-cols-12 gap-4 px-4 py-3 border-b border-white/10 bg-black/60 font-jetbrains text-[10px] uppercase tracking-widest text-white/50">
        <div className="col-span-3">Kullanıcı</div>
        <div className="col-span-3">Email</div>
        <div className="col-span-2">Rol</div>
        <div className="col-span-1">Eğitim</div>
        <div className="col-span-3 text-right">İşlem</div>
      </div>
      {users.map(u => (
        <div key={u.user_id} data-testid={`user-row-${u.user_id}`} className="grid grid-cols-1 md:grid-cols-12 gap-3 md:gap-4 px-4 py-4 border-b border-white/5 last:border-b-0 items-center">
          <div className="col-span-3 flex items-center gap-3">
            {u.picture ? <img src={u.picture} alt="" className="w-9 h-9 border border-white/10" /> : <div className="w-9 h-9 bg-[#F59E0B] text-black flex items-center justify-center font-jetbrains font-bold">{u.name?.[0]?.toUpperCase()}</div>}
            <p className="text-white font-outfit font-semibold truncate">{u.name}</p>
          </div>
          <div className="col-span-3 text-white/60 text-sm truncate">{u.email}</div>
          <div className="col-span-2">
            <span className={`inline-block px-2 py-0.5 font-jetbrains text-[10px] uppercase tracking-widest ${u.role === "admin" ? "bg-[#10B981] text-black" : "border border-white/20 text-white/70"}`}>
              {u.role}
            </span>
          </div>
          <div className="col-span-1">
            {u.education_access ? (
              <span className="inline-flex items-center gap-1 text-[#F59E0B] font-jetbrains text-[10px] uppercase tracking-widest"><Check size={12} /> Var</span>
            ) : (
              <span className="inline-flex items-center gap-1 text-white/40 font-jetbrains text-[10px] uppercase tracking-widest"><X size={12} /> Yok</span>
            )}
          </div>
          <div className="col-span-3 flex md:justify-end gap-2 flex-wrap">
            <button data-testid={`toggle-edu-${u.user_id}`} onClick={() => toggleEdu(u)} className={`px-3 py-1.5 border font-jetbrains text-[10px] uppercase tracking-widest inline-flex items-center gap-1 ${u.education_access ? "border-[#F59E0B] text-[#F59E0B]" : "border-white/10 text-white/70 hover:border-[#F59E0B] hover:text-[#F59E0B]"}`}>
              <GraduationCap size={12} /> {u.education_access ? "Eğitim kaldır" : "Eğitim ver"}
            </button>
            {u.role === "writer" || u.role === "user" ? (
              <button data-testid={`promote-${u.user_id}`} onClick={() => changeRole(u, "admin")} className="px-3 py-1.5 border border-white/10 hover:border-[#10B981] text-white/70 hover:text-[#10B981] font-jetbrains text-[10px] uppercase tracking-widest inline-flex items-center gap-1">
                <Shield size={12} /> Admin
              </button>
            ) : (
              <button data-testid={`demote-${u.user_id}`} onClick={() => changeRole(u, "user")} className="px-3 py-1.5 border border-white/10 hover:border-white text-white/70 hover:text-white font-jetbrains text-[10px] uppercase tracking-widest">
                User
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

const EducationTab = () => {
  const [members, setMembers] = useState([]);
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");
  const load = () => api.get("/admin/education-members").then(r => setMembers(r.data || []));
  useEffect(() => { load(); }, []);

  const add = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    try {
      await api.post("/admin/education-members", { email: email.trim(), note: note.trim() });
      toast.success("Üye eklendi");
      setEmail(""); setNote("");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Eklenemedi");
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Bu üyenin eğitim erişimi kaldırılsın mı?")) return;
    await api.delete(`/admin/education-members/${id}`);
    toast.success("Kaldırıldı");
    load();
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6" data-testid="education-tab">
      <form onSubmit={add} className="md:col-span-1 border border-white/10 p-5 space-y-3" data-testid="edu-add-form">
        <div className="flex items-center gap-2">
          <GraduationCap size={16} className="text-[#F59E0B]" />
          <h3 className="font-outfit font-bold text-white">Yeni Eğitim Üyesi</h3>
        </div>
        <p className="text-white/50 text-xs font-jetbrains uppercase tracking-widest">
          Bu email ile giriş yapan kullanıcı eğitim içeriklerine erişebilir
        </p>
        <input data-testid="edu-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" className="w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white placeholder:text-white/30" />
        <input data-testid="edu-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Not (opsiyonel) — örn: Ekim 2026 grubu" className="w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white placeholder:text-white/30" />
        <Button type="submit" data-testid="edu-add-submit" className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest">
          <PlusCircle size={14} className="mr-2" /> Ekle
        </Button>
        <p className="text-white/40 text-[10px] font-jetbrains uppercase tracking-widest pt-2 border-t border-white/5">
          {members.length} üye · toplam
        </p>
      </form>

      <div className="md:col-span-2 border border-white/10">
        <div className="hidden md:grid grid-cols-12 gap-3 px-4 py-3 border-b border-white/10 bg-black/60 font-jetbrains text-[10px] uppercase tracking-widest text-white/50">
          <div className="col-span-5">Email</div>
          <div className="col-span-4">Not</div>
          <div className="col-span-2">Eklendi</div>
          <div className="col-span-1"></div>
        </div>
        {members.length === 0 ? (
          <div className="p-8 text-center text-white/40 font-jetbrains text-xs uppercase tracking-widest">Henüz üye yok. Sol taraftan ekleyin.</div>
        ) : members.map(m => (
          <div key={m.id} data-testid={`edu-row-${m.id}`} className="grid grid-cols-1 md:grid-cols-12 gap-3 px-4 py-3 border-b border-white/5 last:border-b-0 items-center">
            <div className="col-span-5 text-white font-jetbrains text-sm truncate">{m.email}</div>
            <div className="col-span-4 text-white/60 text-sm truncate">{m.note || "—"}</div>
            <div className="col-span-2 text-white/40 font-jetbrains text-[10px] uppercase tracking-widest">{new Date(m.added_at).toLocaleDateString("tr-TR")}</div>
            <div className="col-span-1 flex md:justify-end">
              <button data-testid={`edu-del-${m.id}`} onClick={() => remove(m.id)} className="p-2 border border-white/10 hover:border-[#EF4444] text-white/70 hover:text-[#EF4444]"><Trash2 size={14} /></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const CategoriesTab = () => {
  const [cats, setCats] = useState([]);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const load = () => api.get("/categories").then(r => setCats(r.data || []));
  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api.post("/admin/categories", { name, description: desc });
      toast.success("Kategori eklendi");
      setName(""); setDesc("");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Hata");
    }
  };
  const del = async (id) => {
    if (!window.confirm("Silinsin mi?")) return;
    await api.delete(`/admin/categories/${id}`);
    load();
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <form onSubmit={create} className="md:col-span-1 border border-white/10 p-5 space-y-3" data-testid="new-category-form">
        <h3 className="font-outfit font-bold text-white">Yeni Kategori</h3>
        <input data-testid="new-cat-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Kategori adı" className="w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm" />
        <textarea data-testid="new-cat-desc" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Açıklama" rows={3} className="w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm" />
        <Button type="submit" data-testid="new-cat-submit" className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest">Ekle</Button>
      </form>

      <div className="md:col-span-2 border border-white/10">
        {cats.map(c => (
          <div key={c.id} data-testid={`cat-row-${c.id}`} className="flex items-center justify-between px-4 py-3 border-b border-white/5 last:border-b-0">
            <div>
              <p className="font-outfit font-semibold text-white">{c.name}</p>
              <p className="font-jetbrains text-[10px] uppercase tracking-widest text-white/40">/{c.slug} · {c.description}</p>
            </div>
            <button data-testid={`delete-cat-${c.id}`} onClick={() => del(c.id)} className="p-2 border border-white/10 hover:border-[#EF4444] text-white/70 hover:text-[#EF4444]"><Trash2 size={14} /></button>
          </div>
        ))}
      </div>
    </div>
  );
};


const ProfileTab = ({ user }) => {
  const [name, setName] = useState(user.name || "");
  const [bio, setBio] = useState(user.bio || "");
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saving, setSaving] = useState(false);
  const [changing, setChanging] = useState(false);

  const isGoogle = user.provider === "google";

  const saveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch("/auth/profile", { name, bio });
      toast.success("Profil güncellendi");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Hata");
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    if (next !== confirm) return toast.error("Yeni şifreler eşleşmiyor");
    if (next.length < 8) return toast.error("Yeni şifre en az 8 karakter");
    setChanging(true);
    try {
      await api.post("/auth/change-password", { current_password: current, new_password: next });
      toast.success("Şifre değiştirildi");
      setCurrent(""); setNext(""); setConfirm("");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Şifre değişmedi");
    } finally {
      setChanging(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="profile-tab">
      <form onSubmit={saveProfile} className="border border-white/10 p-5 space-y-3">
        <h3 className="font-outfit font-bold text-white">Profil Bilgileri</h3>
        <p className="text-white/50 text-xs font-jetbrains uppercase tracking-widest">Görünen ad ve biyografi</p>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Ad</label>
          <input data-testid="profile-name" value={name} onChange={e => setName(e.target.value)} className="mt-2 w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white" />
        </div>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Biyografi</label>
          <textarea data-testid="profile-bio" value={bio} onChange={e => setBio(e.target.value)} rows={3} className="mt-2 w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white" />
        </div>
        <Button type="submit" data-testid="profile-save" disabled={saving} className="w-full bg-white/10 hover:bg-white/20 text-white rounded-none font-jetbrains text-[11px] uppercase tracking-widest">
          <Save size={14} className="mr-2" /> Kaydet
        </Button>
        <p className="pt-3 border-t border-white/5 font-jetbrains text-[10px] uppercase tracking-widest text-white/40">
          Email: <span className="text-white/70">{user.email}</span><br />
          Sağlayıcı: <span className="text-white/70">{user.provider}</span>
        </p>
      </form>

      <form onSubmit={changePassword} className="border border-white/10 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <KeyRound size={16} className="text-[#F59E0B]" />
          <h3 className="font-outfit font-bold text-white">Şifre Değiştir</h3>
        </div>
        {isGoogle ? (
          <p className="text-white/50 text-xs font-jetbrains">Google hesabıyla giriş yaptığınız için burada bir şifre belirleyerek email/şifre ile de giriş yapabilirsiniz. Mevcut şifreyi boş bırakın.</p>
        ) : (
          <p className="text-white/50 text-xs font-jetbrains uppercase tracking-widest">Mevcut şifreniz ile yeni şifreyi belirleyin</p>
        )}
        {user.must_change_password && (
          <div className="border border-[#F59E0B]/40 bg-[#F59E0B]/10 p-2 text-[#F59E0B] font-jetbrains text-[10px] uppercase tracking-widest">
            ⚠️ İlk giriş — Lütfen varsayılan şifreyi değiştirin
          </div>
        )}
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Mevcut Şifre</label>
          <input data-testid="cp-current" type="password" value={current} onChange={e => setCurrent(e.target.value)} className="mt-2 w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white" />
        </div>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Yeni Şifre</label>
          <input data-testid="cp-new" type="password" minLength={8} value={next} onChange={e => setNext(e.target.value)} className="mt-2 w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white" />
        </div>
        <div>
          <label className="font-jetbrains text-[10px] uppercase tracking-widest text-[#F59E0B]">Yeni Şifre (Tekrar)</label>
          <input data-testid="cp-confirm" type="password" minLength={8} value={confirm} onChange={e => setConfirm(e.target.value)} className="mt-2 w-full bg-black border border-white/10 px-3 py-2 outline-none focus:border-[#F59E0B] font-jetbrains text-sm text-white" />
        </div>
        <Button type="submit" data-testid="cp-submit" disabled={changing} className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-black rounded-none font-jetbrains text-[11px] uppercase tracking-widest">
          <KeyRound size={14} className="mr-2" /> Şifreyi Güncelle
        </Button>
      </form>
    </div>
  );
};
