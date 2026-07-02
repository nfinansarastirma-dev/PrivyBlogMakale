import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import { Youtube } from "@tiptap/extension-youtube";
import { useRef } from "react";
import {
  Bold, Italic, Underline as UIcon, Heading1, Heading2, Heading3, List, ListOrdered,
  Quote, Code, Link as LinkIcon, Image as ImageIcon, Undo, Redo, Minus, Youtube as YoutubeIcon
} from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

const Btn = ({ onClick, active, children, tid, disabled }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    data-testid={tid}
    className={`p-2 border border-white/10 hover:border-[#F59E0B] hover:text-[#F59E0B] transition-colors ${active ? "bg-[#F59E0B] text-black border-[#F59E0B]" : "text-white/70"} disabled:opacity-30`}
  >
    {children}
  </button>
);

export const RichEditor = ({ value, onChange, placeholder = "Makalenizi buraya yazın..." }) => {
  const fileRef = useRef(null);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        link: { openOnClick: false, autolink: true, HTMLAttributes: { rel: "noopener noreferrer nofollow", target: "_blank" } },
      }),
      Image.configure({ inline: false, allowBase64: false }),
      Placeholder.configure({ placeholder }),
      Youtube.configure({ controls: true, nocookie: true, width: 720, height: 405, HTMLAttributes: { class: "yt-embed" } }),
    ],
    content: value || "",
    onUpdate: ({ editor }) => onChange?.(editor.getHTML()),
    editorProps: { attributes: { class: "prose prose-invert max-w-none" } },
  });

  if (!editor) return null;

  const promptLink = () => {
    const previous = editor.getAttributes("link").href;
    const url = window.prompt("Bağlantı URL:", previous || "https://");
    if (url === null) return;
    if (url === "") {
      editor.chain().focus().unsetLink().run();
    } else {
      editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
    }
  };

  const uploadImage = async (file) => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      const url = `${process.env.REACT_APP_BACKEND_URL}${data.url}`;
      editor.chain().focus().setImage({ src: url, alt: file.name }).run();
      toast.success("Görsel eklendi");
    } catch (e) {
      toast.error("Görsel yüklenemedi");
    }
  };

  const addYoutube = () => {
    const url = window.prompt("YouTube URL:", "https://www.youtube.com/watch?v=");
    if (!url) return;
    try {
      editor.chain().focus().setYoutubeVideo({ src: url, width: 720, height: 405 }).run();
    } catch (e) {
      toast.error("Geçersiz YouTube linki");
    }
  };

  return (
    <div className="border border-white/10 bg-[#0A0A0A]" data-testid="rich-editor">
      <div className="flex flex-wrap gap-1 p-2 border-b border-white/10 bg-black/60 sticky top-0 z-10">
        <Btn tid="rt-bold" onClick={() => editor.chain().focus().toggleBold().run()} active={editor.isActive("bold")}><Bold size={14} /></Btn>
        <Btn tid="rt-italic" onClick={() => editor.chain().focus().toggleItalic().run()} active={editor.isActive("italic")}><Italic size={14} /></Btn>
        <Btn tid="rt-underline" onClick={() => editor.chain().focus().toggleUnderline().run()} active={editor.isActive("underline")}><UIcon size={14} /></Btn>
        <span className="w-px bg-white/10 mx-1" />
        <Btn tid="rt-h1" onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} active={editor.isActive("heading", { level: 1 })}><Heading1 size={14} /></Btn>
        <Btn tid="rt-h2" onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} active={editor.isActive("heading", { level: 2 })}><Heading2 size={14} /></Btn>
        <Btn tid="rt-h3" onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} active={editor.isActive("heading", { level: 3 })}><Heading3 size={14} /></Btn>
        <span className="w-px bg-white/10 mx-1" />
        <Btn tid="rt-ul" onClick={() => editor.chain().focus().toggleBulletList().run()} active={editor.isActive("bulletList")}><List size={14} /></Btn>
        <Btn tid="rt-ol" onClick={() => editor.chain().focus().toggleOrderedList().run()} active={editor.isActive("orderedList")}><ListOrdered size={14} /></Btn>
        <Btn tid="rt-quote" onClick={() => editor.chain().focus().toggleBlockquote().run()} active={editor.isActive("blockquote")}><Quote size={14} /></Btn>
        <Btn tid="rt-code" onClick={() => editor.chain().focus().toggleCodeBlock().run()} active={editor.isActive("codeBlock")}><Code size={14} /></Btn>
        <span className="w-px bg-white/10 mx-1" />
        <Btn tid="rt-link" onClick={promptLink} active={editor.isActive("link")}><LinkIcon size={14} /></Btn>
        <Btn tid="rt-image" onClick={() => fileRef.current?.click()}><ImageIcon size={14} /></Btn>
        <Btn tid="rt-youtube" onClick={addYoutube}><YoutubeIcon size={14} /></Btn>
        <Btn tid="rt-hr" onClick={() => editor.chain().focus().setHorizontalRule().run()}><Minus size={14} /></Btn>
        <span className="w-px bg-white/10 mx-1" />
        <Btn tid="rt-undo" onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()}><Undo size={14} /></Btn>
        <Btn tid="rt-redo" onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()}><Redo size={14} /></Btn>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          data-testid="rt-image-input"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadImage(f); e.target.value = ""; }}
        />
      </div>
      <div className="tiptap-editor p-5 min-h-[400px]">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
};
