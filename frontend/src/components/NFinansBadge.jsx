export const NFinansBadge = () => {
  return (
    <a
      href="https://www.nfinans.net/"
      target="_blank"
      rel="noopener noreferrer"
      data-testid="nfinans-badge"
      className="fixed bottom-4 right-4 z-[9999] inline-flex items-center gap-2 bg-black/90 backdrop-blur-xl border border-white/10 hover:border-[#F59E0B] px-4 py-2 font-jetbrains text-xs text-white hover:text-[#F59E0B] transition-colors shadow-xl"
      style={{ borderRadius: 9999 }}
    >
      <span className="inline-flex items-center justify-center w-5 h-5 border border-current rounded-full font-bold text-[10px]">©</span>
      <span>Made with nFinans</span>
    </a>
  );
};
