"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/app/providers";
import { BookOpen } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <BookOpen className="w-10 h-10 text-lore-gold mx-auto mb-3" />
          <h1 className="text-2xl font-bold">Welcome Back</h1>
          <p className="text-sm text-lore-text-muted mt-1">
            Sign in to your lore vault
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-lore-text-muted mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-lore-card border border-lore-border text-lore-text placeholder:text-lore-text-muted/40 focus:outline-none focus:ring-2 focus:ring-lore-gold/30 focus:border-lore-gold transition-all"
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-lore-text-muted mb-1.5">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-lore-card border border-lore-border text-lore-text placeholder:text-lore-text-muted/40 focus:outline-none focus:ring-2 focus:ring-lore-gold/30 focus:border-lore-gold transition-all"
              placeholder="Your password"
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-lore-gold text-black font-semibold hover:bg-lore-gold-dark disabled:opacity-50 transition-colors"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="text-center text-sm text-lore-text-muted mt-6">
          Don't have an account?{" "}
          <Link href="/register" className="text-lore-gold hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
