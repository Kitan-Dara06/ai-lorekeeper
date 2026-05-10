"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import { getSnapshots } from "@/lib/api";
import { History, Sparkles, Clock } from "lucide-react";

export default function LoreHistoryPage() {
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSnapshots()
      .then((data) => setSnapshots(data.snapshots))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <AuthGuard>
      <div className="max-w-4xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <History className="w-7 h-7 text-lore-gold" />
            Lore History
          </h1>
          <p className="text-lore-text-muted mt-1">
            Every synthesis run creates a permanent snapshot of your lore
          </p>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="lore-card animate-pulse h-24" />
            ))}
          </div>
        ) : snapshots.length === 0 ? (
          <div className="lore-card text-center py-16">
            <Sparkles className="w-12 h-12 text-lore-text-muted mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">No Lore Yet</h2>
            <p className="text-lore-text-muted text-sm mb-6">
              Upload files to your vault and run a synthesis to generate your
              first lore snapshot.
            </p>
            <Link
              href="/vault"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-lore-gold text-black font-semibold hover:bg-lore-gold-dark transition-colors text-sm"
            >
              Go to Vault
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {snapshots.map((snap: any) => (
              <Link
                key={snap.id}
                href={`/lore/${snap.id}`}
                className="lore-card block hover:border-lore-purple/40 transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-base font-display italic leading-relaxed mb-2">
                      &ldquo;{snap.the_sentence}&rdquo;
                    </p>
                    <div className="flex items-center gap-3 text-xs text-lore-text-muted">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(snap.created_at).toLocaleDateString(
                          undefined,
                          {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          },
                        )}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          snap.status === "completed"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : snap.status === "running"
                              ? "bg-amber-500/10 text-amber-400"
                              : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {snap.status}
                      </span>
                    </div>
                  </div>
                  <Sparkles className="w-5 h-5 text-lore-purple shrink-0 mt-1" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
