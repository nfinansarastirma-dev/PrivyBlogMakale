import { useEffect, useState } from "react";
import Marquee from "react-fast-marquee";
import { api } from "@/lib/api";

const signalClass = (signal) => {
  if (!signal) return "ticker-signal-neutral";
  const s = signal.toUpperCase();
  if (s.includes("AL") || s.includes("BULL") || s.includes("POZ")) return "ticker-signal-buy";
  if (s.includes("SAT") || s.includes("BEAR") || s.includes("DOWN")) return "ticker-signal-sell";
  return "ticker-signal-neutral";
};

export const Ticker = () => {
  const [items, setItems] = useState([]);
  useEffect(() => {
    api.get("/ticker").then(r => setItems(r.data.items || [])).catch(() => {});
  }, []);
  if (!items.length) return null;
  return (
    <div
      data-testid="market-ticker"
      className="bg-[#050505] border-b border-white/10 py-2 font-jetbrains text-[11px] uppercase tracking-wider"
    >
      <Marquee speed={45} gradient={false} pauseOnHover>
        {items.map((it, i) => (
          <span key={i} className="mx-6 inline-flex items-center gap-2" data-testid={`ticker-item-${i}`}>
            <span className="text-white/60">{it.symbol}</span>
            <span className="text-white">{it.price}</span>
            <span className={signalClass(it.signal)}>{it.change}</span>
            <span className={`px-2 py-0.5 border border-white/10 ${signalClass(it.signal)}`}>
              {it.signal}
            </span>
            <span className="text-white/20">·</span>
          </span>
        ))}
      </Marquee>
    </div>
  );
};
