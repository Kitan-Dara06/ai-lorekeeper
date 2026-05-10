"use client";

import Link from "next/link";
import { useAuth } from "@/app/providers";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  Menu,
  X,
  Sparkles,
  LogOut,
  BookOpen,
  FolderOpen,
  History,
} from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const navLinks = user
    ? [
        { href: "/dashboard", label: "Dashboard", icon: Sparkles },
        { href: "/vault", label: "Vault", icon: FolderOpen },
        { href: "/lore", label: "Lore History", icon: History },
      ]
    : [];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-lore-dark/80 backdrop-blur-md border-b border-lore-border">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <BookOpen className="w-6 h-6 text-lore-gold group-hover:rotate-6 transition-transform" />
          <span className="font-bold text-lg gradient-text">AI Lorekeeper</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-lore-text-muted hover:text-lore-text transition-colors flex items-center gap-1.5"
            >
              <link.icon className="w-4 h-4" />
              {link.label}
            </Link>
          ))}
          {user && (
            <>
              <span className="text-sm text-lore-text-muted/60 px-2">|</span>
              <span className="text-sm text-lore-text-muted">{user.email}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-red-400 hover:text-red-300 transition-colors flex items-center gap-1"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-lore-text p-2"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? (
            <X className="w-5 h-5" />
          ) : (
            <Menu className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-lore-border bg-lore-darker/95 backdrop-blur-md">
          <div className="px-4 py-3 space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="block py-2 text-sm text-lore-text-muted hover:text-lore-text flex items-center gap-2"
              >
                <link.icon className="w-4 h-4" />
                {link.label}
              </Link>
            ))}
            {user && (
              <div className="pt-2 border-t border-lore-border mt-2">
                <p className="text-xs text-lore-text-muted/60 mb-2">
                  {user.email}
                </p>
                <button
                  onClick={() => {
                    handleLogout();
                    setMobileOpen(false);
                  }}
                  className="text-sm text-red-400 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" /> Logout
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
