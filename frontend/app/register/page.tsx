"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/app/providers";
import { BookOpen } from "lucide-react";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    try {
      await register(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <BookOpen className="w-10 h-10 text-lore-gold mx-auto mb-3" />
          <h1 className="text-2xl font-bold">Create Your Vault</h1>
          <p className="text-sm text-lore-text-muted mt-1">
            Start your lore journey
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
              placeholder="Min 6 characters"
              required
              minLength={6}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-lore-text-muted mb-1.5">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-lore-card border border-lore-border text-lore-text placeholder:text-lore-text-muted/40 focus:outline-none focus:ring-2 focus:ring-lore-gold/30 focus:border-lore-gold transition-all"
              placeholder="Repeat your password"
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-lore-gold text-black font-semibold hover:bg-lore-gold-dark disabled:opacity-50 transition-colors"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-sm text-lore-text-muted mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-lore-gold hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
