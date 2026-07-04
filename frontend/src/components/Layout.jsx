import { Ticker } from "@/components/Ticker";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { NFinansBadge } from "@/components/NFinansBadge";

export const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#050505] text-white flex flex-col">
      <Ticker />
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
      <NFinansBadge />
    </div>
  );
};
