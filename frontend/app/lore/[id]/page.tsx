"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import { getSnapshotDetail } from "@/lib/api";
import {
  ArrowLeft,
  ArrowRight,
  Copy,
  Check,
  FileText,
  Users,
  Zap,
  Repeat,
  Tag,
  AlertTriangle,
  BookOpen,
  Star,
} from "lucide-react";

export default function LoreDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [lore, setLore] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!id) return;
    getSnapshotDetail(id)
      .then(setLore)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const copyNarrative = async () => {
    if (!lore?.narrative) return;
    try {
      await navigator.clipboard.writeText(lore.narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const handleExportPdf = () => {
    window.print();
  };

  if (loading) {
    return (
      <AuthGuard>
        <div className="max-w-4xl mx-auto px-4 py-10">
          <div className="animate-pulse space-y-6">
            <div className="h-12 bg-lore-card rounded-xl" />
            <div className="h-64 bg-lore-card rounded-xl" />
            <div className="h-40 bg-lore-card rounded-xl" />
          </div>
        </div>
      </AuthGuard>
    );
  }

  if (error || !lore) {
    return (
      <AuthGuard>
        <div className="max-w-4xl mx-auto px-4 py-10 text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Snapshot Not Found</h2>
          <p className="text-lore-text-muted mb-6">
            {error || "This lore snapshot could not be found."}
          </p>
          <Link href="/lore" className="text-lore-gold hover:underline">
            Back to Lore History
          </Link>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="max-w-4xl mx-auto px-4 py-10">
        {/* Navigation */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => router.push("/lore")}
            className="flex items-center gap-1.5 text-sm text-lore-text-muted hover:text-lore-text transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to History
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={copyNarrative}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-lore-border text-xs text-lore-text-muted hover:text-lore-text hover:bg-lore-card transition-colors"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
              {copied ? "Copied!" : "Copy Narrative"}
            </button>
            <button
              onClick={handleExportPdf}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-lore-border text-xs text-lore-text-muted hover:text-lore-text hover:bg-lore-card transition-colors"
            >
              <FileText className="w-3.5 h-3.5" /> Export PDF
            </button>
          </div>
        </div>

        {/* The Sentence — prominent */}
        <div className="text-center mb-12 animate-fade-in-up">
          <p className="text-xs text-lore-text-muted uppercase tracking-widest mb-4">
            The Sentence
          </p>
          <div className="gradient-border p-8 md:p-10 inline-block max-w-2xl mx-auto">
            <p className="text-xl md:text-2xl lg:text-3xl font-display italic leading-relaxed">
              &ldquo;{lore.the_sentence}&rdquo;
            </p>
          </div>
        </div>

        {/* Narrative */}
        <div className="lore-card mb-10">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-lore-gold" /> Narrative
          </h2>
          <div className="text-lore-text leading-relaxed whitespace-pre-line font-display text-base">
            {lore.narrative}
          </div>
        </div>

        {/* Story Arcs */}
        <Section
          title="Story Arcs"
          icon={<Zap className="w-5 h-5 text-lore-gold" />}
        >
          <div className="grid sm:grid-cols-2 gap-4">
            {lore.story_arcs?.map((arc: any, i: number) => (
              <div key={i} className="lore-card">
                <h3 className="font-semibold text-lore-gold mb-2">
                  {arc.title}
                </h3>
                <p className="text-sm text-lore-text-muted">
                  {arc.description}
                </p>
              </div>
            ))}
          </div>
        </Section>

        {/* Recurring People */}
        <Section
          title="Recurring People"
          icon={<Users className="w-5 h-5 text-lore-teal" />}
        >
          <div className="flex flex-wrap gap-3">
            {lore.recurring_people?.map((p: any, i: number) => (
              <div
                key={i}
                className="group relative lore-card py-2 px-4 cursor-default"
              >
                <span className="text-sm font-medium text-lore-teal">
                  {p.identifier}
                </span>
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 rounded-xl bg-lore-card border border-lore-border text-xs text-lore-text-muted opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
                  {p.context}
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Defining Moments */}
        <Section
          title="Defining Moments"
          icon={<Star className="w-5 h-5 text-lore-pink" />}
        >
          <div className="space-y-4">
            {lore.defining_moments?.map((m: any, i: number) => (
              <div key={i} className="lore-card border-l-2 border-l-lore-pink">
                <h3 className="font-semibold text-sm mb-1">{m.moment}</h3>
                <p className="text-xs text-lore-text-muted">{m.significance}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Mindset Shifts */}
        <Section
          title="Mindset Shifts"
          icon={<Repeat className="w-5 h-5 text-lore-purple" />}
        >
          <div className="space-y-4">
            {lore.mindset_shifts?.map((s: any, i: number) => (
              <div key={i} className="lore-card">
                <p className="text-xs text-lore-text-muted mb-2">{s.period}</p>
                <div className="flex items-center gap-3">
                  <div className="flex-1 p-3 rounded-lg bg-red-500/5 border border-red-500/10">
                    <p className="text-xs text-lore-text-muted mb-0.5">From</p>
                    <p className="text-sm font-medium text-red-400">
                      {s.from_state}
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-lore-purple shrink-0" />
                  <div className="flex-1 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                    <p className="text-xs text-lore-text-muted mb-0.5">To</p>
                    <p className="text-sm font-medium text-emerald-400">
                      {s.to_state}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-lore-text-muted mt-2 italic">
                  {s.evidence}
                </p>
              </div>
            ))}
          </div>
        </Section>

        {/* Core Themes */}
        <Section
          title="Core Themes"
          icon={<Tag className="w-5 h-5 text-lore-gold" />}
        >
          <div className="flex flex-wrap gap-2">
            {lore.core_themes?.map((theme: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1.5 rounded-full bg-lore-purple/10 border border-lore-purple/20 text-lore-purple text-sm"
              >
                {theme}
              </span>
            ))}
          </div>
        </Section>

        {/* Identity Contradictions — most visually distinctive */}
        <Section
          title="Identity Contradictions"
          icon={<AlertTriangle className="w-5 h-5 text-amber-400" />}
        >
          <div className="space-y-4">
            {lore.identity_contradictions?.map((c: any, i: number) => (
              <div
                key={i}
                className="lore-card border border-amber-500/20 bg-amber-500/5"
              >
                <p className="text-sm font-semibold text-amber-300 mb-2">
                  {c.observation}
                </p>
                <div className="grid sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-red-500/5 border border-red-500/10">
                    <span className="text-red-400 font-medium">Evidence: </span>
                    <span className="text-lore-text-muted">{c.evidence}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-lore-purple/5 border border-lore-purple/10">
                    <span className="text-lore-purple font-medium">
                      Interpretation:{" "}
                    </span>
                    <span className="text-lore-text-muted">
                      {c.interpretation}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Meta */}
        <div className="text-center text-xs text-lore-text-muted mt-10">
          Generated on{" "}
          {new Date(lore.created_at).toLocaleDateString(undefined, {
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
          {" · "}
          {lore.file_count} file{lore.file_count !== 1 ? "s" : ""} analyzed
        </div>
      </div>
    </AuthGuard>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-10">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        {icon} {title}
      </h2>
      {children}
    </div>
  );
}
