"use client";

import Link from "next/link";
import { useAuth } from "./providers";
import {
  ArrowRight,
  Upload,
  Brain,
  Sparkles,
  BookOpen,
  Image as ImageIcon,
} from "lucide-react";

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center px-4 py-32 text-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-lore-purple/5 via-transparent to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-lore-purple/10 border border-lore-purple/20 text-lore-purple text-xs font-medium mb-8">
            <Sparkles className="w-3.5 h-3.5" /> Built for the Gemma 4 Challenge
          </div>
          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
            Your Life,
            <br />
            <span className="gradient-text">Synthesized</span>
          </h1>
          <p className="text-lg md:text-xl text-lore-text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload fragments of your digital life — chat exports, journal
            entries, screenshots, photos — and AI transforms them into
            structured narrative: story arcs, recurring themes, emotional
            patterns, and mindset shifts.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {user ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-lore-gold text-black font-semibold hover:bg-lore-gold-dark transition-colors"
              >
                Go to Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-lore-gold text-black font-semibold hover:bg-lore-gold-dark transition-colors"
                >
                  Get Started <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl border border-lore-border text-lore-text hover:bg-lore-card transition-colors"
                >
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 pb-32">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="lore-card text-center">
            <div className="w-12 h-12 rounded-xl bg-lore-purple/10 flex items-center justify-center mx-auto mb-4">
              <Upload className="w-5 h-5 text-lore-purple" />
            </div>
            <h3 className="font-semibold mb-2">Upload Any Format</h3>
            <p className="text-sm text-lore-text-muted">
              TXT, PDF, MD, JSON, CSV, and images. Your data, your way.
            </p>
          </div>
          <div className="lore-card text-center">
            <div className="w-12 h-12 rounded-xl bg-lore-gold/10 flex items-center justify-center mx-auto mb-4">
              <Brain className="w-5 h-5 text-lore-gold" />
            </div>
            <h3 className="font-semibold mb-2">AI-Powered Synthesis</h3>
            <p className="text-sm text-lore-text-muted">
              Gemma 4 transforms raw data into structured narrative insights.
            </p>
          </div>
          <div className="lore-card text-center">
            <div className="w-12 h-12 rounded-xl bg-lore-teal/10 flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-5 h-5 text-lore-teal" />
            </div>
            <h3 className="font-semibold mb-2">Visual Lore Cards</h3>
            <p className="text-sm text-lore-text-muted">
              Story arcs, recurring people, mindset shifts, and more.
            </p>
          </div>
          <div className="lore-card text-center">
            <div className="w-12 h-12 rounded-xl bg-lore-pink/10 flex items-center justify-center mx-auto mb-4">
              <ImageIcon className="w-5 h-5 text-lore-pink" />
            </div>
            <h3 className="font-semibold mb-2">See Your Evolution</h3>
            <p className="text-sm text-lore-text-muted">
              Every synthesis run creates a snapshot. Watch your lore grow.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-lore-border py-8 text-center">
        <p className="text-sm text-lore-text-muted">
          Built for the{" "}
          <span className="text-lore-gold">Gemma 4 Challenge</span> — Build
          Track
        </p>
      </footer>
    </div>
  );
}
