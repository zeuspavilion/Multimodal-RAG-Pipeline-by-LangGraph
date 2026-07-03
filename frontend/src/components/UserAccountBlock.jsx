import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MoreVertical, Settings, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function UserAccountBlock() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpen]);

  if (!user) return null;

  const initials = user.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "??";

  function handleLogout() {
    setMenuOpen(false);
    logout();
    navigate("/login");
  }

  return (
    <div className="relative border-t border-[var(--border-light)] p-2.5" ref={menuRef}>
      <button
        id="user-account-block"
        onClick={() => setMenuOpen((prev) => !prev)}
        className="w-full p-2 flex items-center gap-3 bg-transparent text-[var(--foreground)] cursor-pointer border-none hover:bg-[var(--brand-hover-bg)]/50 rounded-xl transition-colors duration-100"
      >
        {/* Circle Avatar */}
        <div
          className="w-8 h-8 rounded-full bg-[var(--brand-terracotta)] text-white flex items-center justify-center shrink-0 font-semibold shadow-sm select-none"
          style={{ fontFamily: '"Inter", sans-serif', fontSize: "11px" }}
        >
          {initials}
        </div>

        {/* Name + email */}
        <div className="flex-1 text-left min-w-0">
          <div
            className="text-xs font-bold truncate text-[var(--foreground)]"
            style={{ fontFamily: '"Inter", sans-serif' }}
          >
            {user.name}
          </div>
          <div
            className="text-[10px] text-[var(--muted-foreground)] truncate"
            style={{ fontFamily: '"Inter", sans-serif' }}
          >
            {user.email}
          </div>
        </div>

        {/* More icon */}
        <MoreVertical size={14} className="text-[var(--muted-foreground)] shrink-0 opacity-70" />
      </button>

      {/* Dropdown menu - Claude styled */}
      {menuOpen && (
        <div className="absolute bottom-full left-3 right-3 mb-2 bg-white border border-[var(--border-light)] rounded-xl shadow-xl z-50 overflow-hidden py-1">
          <button
            disabled
            className="w-full text-left px-4 py-2.5 text-xs text-gray-350 cursor-not-allowed border-none bg-transparent flex items-center gap-2 opacity-50 font-semibold"
            style={{ fontFamily: '"Inter", sans-serif' }}
          >
            <Settings size={13} />
            Account Settings
          </button>
          <div className="h-px bg-[var(--border-light)] my-1" />
          <button
            id="sign-out-button"
            onClick={handleLogout}
            className="w-full text-left px-4 py-2.5 text-xs font-semibold cursor-pointer border-none bg-transparent text-[var(--foreground)] hover:bg-[var(--brand-tan-bg)] flex items-center gap-2 transition-colors duration-100"
            style={{ fontFamily: '"Inter", sans-serif' }}
          >
            <LogOut size={13} className="text-[var(--brand-terracotta)]" />
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
