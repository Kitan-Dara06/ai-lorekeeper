"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import { useAuth } from "@/app/providers";
import { getFiles, getSnapshots, getRuns } from "@/lib/api";
import {
  Sparkles,
  FolderOpen,
  History,
  ArrowRight,
  Upload,
  Brain,
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const [fileCount, setFileCount] = useState(0);
  const [runCount, setRunCount] = useState(0);
  const [snapCount, setSnapCount] = useState(0);
  const [latestSentence, setLatestSentence] = useState<string | null>(null);
  const [recentFiles, setRecentFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getFiles().catch(() => ({ files: [], total: 0 })),
      getSnapshots().catch(() => ({ snapshots: [], total: 0 })),
      getRuns().catch(() => ({ runs: [], total: 0 })),
    ])
      .then(([filesData, snapData, runsData]) => {
        setFileCount(filesData.total);
        setRunCount(runsData.total);
        setSnapCount(snapData.total);
        setRecentFiles(filesData.files.slice(0, 5));
        if (snapData.snapshots.length > 0) {
          setLatestSentence(snapData.snapshots[0].the_sentence);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <AuthGuard>
      <div className="max-w-5xl mx-auto px-4 py-10">
        <div className="mb-10">
          <h1 className="text-3xl font-bold">
            Welcome back,{" "}
            <span className="gradient-text">{user?.email?.split("@")[0]}</span>
          </h1>
          <p className="text-lore-text-muted mt-1">
            Your lore vault at a glance
          </p>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-5 mb-10">
          <div className="lore-card flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-lore-purple/10 flex items-center justify-center shrink-0">
              <FolderOpen className="w-5 h-5 text-lore-purple" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {loading ? "..." : fileCount}
              </p>
              <p className="text-sm text-lore-text-muted">Files in vault</p>
            </div>
          </div>
          <div className="lore-card flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-lore-gold/10 flex items-center justify-center shrink-0">
              <Brain className="w-5 h-5 text-lore-gold" />
            </div>
            <div>
              <p className="text-2xl font-bold">{loading ? "..." : runCount}</p>
              <p className="text-sm text-lore-text-muted">Synthesis runs</p>
            </div>
          </div>
          <div className="lore-card flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-lore-teal/10 flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-lore-teal" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {loading ? "..." : snapCount > 0 ? "Ready" : "Empty"}
              </p>
              <p className="text-sm text-lore-text-muted">Latest snapshot</p>
            </div>
          </div>
        </div>

        {/* Quick actions */}
        <div className="flex flex-wrap gap-3 mb-10">
          <Link
            href="/vault"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-lore-gold text-black font-semibold hover:bg-lore-gold-dark transition-colors text-sm"
          >
            <Upload className="w-4 h-4" /> Upload Files
          </Link>
          <Link
            href="/vault"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-lore-border hover:bg-lore-card transition-colors text-sm"
          >
            <Sparkles className="w-4 h-4" /> Run Synthesis
          </Link>
          <Link
            href="/lore"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-lore-border hover:bg-lore-card transition-colors text-sm"
          >
            <History className="w-4 h-4" /> View Lore History
          </Link>
        </div>

        {/* Latest sentence */}
        {latestSentence && (
          <div className="gradient-border p-6 mb-10">
            <p className="text-xs text-lore-text-muted uppercase tracking-wider mb-2">
              Latest Lore Sentence
            </p>
            <p className="text-lg md:text-xl font-display italic text-lore-text leading-relaxed">
              &ldquo;{latestSentence}&rdquo;
            </p>
          </div>
        )}

        {/* Recent files */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Files</h2>
            <Link
              href="/vault"
              className="text-sm text-lore-gold hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {recentFiles.length === 0 ? (
            <div className="lore-card text-center py-8">
              <Upload className="w-8 h-8 text-lore-text-muted mx-auto mb-3" />
              <p className="text-lore-text-muted text-sm">
                No files yet. Upload your first file to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentFiles.map((f: any) => (
                <div
                  key={f.id}
                  className="lore-card flex items-center justify-between py-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-lore-purple/10 flex items-center justify-center text-xs text-lore-purple uppercase font-bold">
                      {f.file_type}
                    </div>
                    <div>
                      <p className="text-sm font-medium truncate max-w-[200px] sm:max-w-[400px]">
                        {f.filename}
                      </p>
                      <p className="text-xs text-lore-text-muted">
                        {f.source_tag || "No tag"} ·{" "}
                        {f.uploaded_at
                          ? new Date(f.uploaded_at).toLocaleDateString()
                          : ""}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
