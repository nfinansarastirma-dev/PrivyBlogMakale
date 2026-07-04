import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

// Google OAuth backend redirects here with ?token=<jwt>
export const AuthCallback = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { loginWithToken } = useAuth();
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    done.current = true;
    const token = params.get("token");
    const error = params.get("error");
    if (error) {
      navigate(`/login?error=${encodeURIComponent(error)}`, { replace: true });
      return;
    }
    if (!token) {
      navigate("/login", { replace: true });
      return;
    }
    loginWithToken(token).then(() => navigate("/dashboard", { replace: true }));
  }, [params, navigate, loginWithToken]);

  return (
    <div className="min-h-[50vh] flex items-center justify-center">
      <p className="font-jetbrains text-xs uppercase tracking-widest text-white/60">Kimlik doğrulanıyor...</p>
    </div>
  );
};
