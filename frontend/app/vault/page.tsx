"use client";

import { useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import {
  getFiles,
  uploadFile,
  deleteFile,
  triggerSynthesis,
  getRuns,
} from "@/lib/api";
import { useRouter } from "next/navigation";
import { Upload, Trash2, Sparkles, Check, X } from "lucide-react";

const SOURCE_TAGS = [
  "Journal",
  "WhatsApp",
  "Screenshots",
  "Notes",
  "Photos",
  "Other",
];

export default function VaultPage() {
  const router = useRouter();
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [synthesizing, setSynthesizing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);

  // Upload form state
  const [uploadFile_, setUploadFile] = useState<File | null>(null);
  const [sourceTag, setSourceTag] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadFiles = async () => {
    try {
      const data = await getFiles();
      setFiles(data.files);
    } catch (err: any) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleUpload = async () => {
    if (!uploadFile_) return;
    setUploading(true);
    try {
      await uploadFile(
        uploadFile_,
        sourceTag || undefined,
        periodStart ? `${periodStart}-01` : undefined,
        periodEnd ? `${periodEnd}-01` : undefined,
      );
      showToast("File uploaded successfully", "success");
      setUploadFile(null);
      setSourceTag("");
      setPeriodStart("");
      setPeriodEnd("");
      loadFiles();
    } catch (err: any) {
      showToast(err.message, "error");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (fileId: string) => {
    try {
      await deleteFile(fileId);
      showToast("File deleted", "success");
      loadFiles();
    } catch (err: any) {
      showToast(err.message, "error");
    }
  };

  const handleSynthesize = async () => {
    setSynthesizing(true);
    try {
      const ids = selectedIds.size > 0 ? Array.from(selectedIds) : undefined;
      const result = await triggerSynthesis(ids);
      showToast(result.message, "success");
      router.push("/lore");
    } catch (err: any) {
      showToast(err.message, "error");
    } finally {
      setSynthesizing(false);
    }
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  return (
    <AuthGuard>
      <div className="max-w-5xl mx-auto px-4 py-10">
        {/* Toast */}
        {toast && (
          <div
            className={`fixed top-20 right-4 z-50 px-5 py-3 rounded-xl shadow-2xl border text-sm ${
              toast.type === "success"
                ? "bg-emerald-900/80 border-emerald-500/30 text-emerald-100"
                : "bg-red-900/80 border-red-500/30 text-red-100"
            }`}
          >
            {toast.message}
          </div>
        )}

        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Your Vault</h1>
          <button
            onClick={handleSynthesize}
            disabled={synthesizing || files.length === 0}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-lore-purple text-white font-semibold hover:bg-lore-purple-dark disabled:opacity-50 transition-colors text-sm"
          >
            <Sparkles className="w-4 h-4" />
            {synthesizing
              ? "Synthesizing..."
              : selectedIds.size > 0
                ? `Synthesize (${selectedIds.size})`
                : "Synthesize All"}
          </button>
        </div>

        {/* Upload form */}
        <div className="lore-card mb-8">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Upload className="w-4 h-4 text-lore-gold" /> Upload New File
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            <div>
              <label className="block text-xs text-lore-text-muted mb-1">
                File
              </label>
              <input
                type="file"
                accept=".txt,.pdf,.md,.json,.csv,.jpg,.jpeg,.png,.webp"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="w-full text-sm text-lore-text file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-lore-purple/10 file:text-lore-purple file:text-xs file:font-medium hover:file:bg-lore-purple/20"
              />
            </div>
            <div>
              <label className="block text-xs text-lore-text-muted mb-1">
                Source Tag
              </label>
              <select
                value={sourceTag}
                onChange={(e) => setSourceTag(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-lore-dark border border-lore-border text-lore-text text-sm focus:outline-none focus:ring-2 focus:ring-lore-gold/30"
              >
                <option value="">Auto-detect</option>
                {SOURCE_TAGS.map((tag) => (
                  <option key={tag} value={tag}>
                    {tag}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-lore-text-muted mb-1">
                Period Start
              </label>
              <input
                type="month"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-lore-dark border border-lore-border text-lore-text text-sm focus:outline-none focus:ring-2 focus:ring-lore-gold/30"
              />
            </div>
            <div>
              <label className="block text-xs text-lore-text-muted mb-1">
                Period End
              </label>
              <input
                type="month"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-lore-dark border border-lore-border text-lore-text text-sm focus:outline-none focus:ring-2 focus:ring-lore-gold/30"
              />
            </div>
          </div>
          <button
            onClick={handleUpload}
            disabled={!uploadFile_ || uploading}
            className="px-5 py-2 rounded-lg bg-lore-gold text-black font-semibold text-sm hover:bg-lore-gold-dark disabled:opacity-50 transition-colors"
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>

        {/* File list */}
        <div>
          <h2 className="font-semibold mb-4">
            {loading
              ? "Loading files..."
              : `${files.length} file${files.length !== 1 ? "s" : ""} in vault`}
          </h2>
          {!loading && files.length === 0 ? (
            <div className="lore-card text-center py-12">
              <Upload className="w-10 h-10 text-lore-text-muted mx-auto mb-3" />
              <p className="text-lore-text-muted">
                Your vault is empty. Upload files to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((f: any) => (
                <div
                  key={f.id}
                  className="lore-card flex items-center gap-3 py-3"
                >
                  <button
                    onClick={() => toggleSelect(f.id)}
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                      selectedIds.has(f.id)
                        ? "bg-lore-purple border-lore-purple"
                        : "border-lore-border hover:border-lore-purple"
                    }`}
                  >
                    {selectedIds.has(f.id) && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </button>
                  <div className="w-8 h-8 rounded-lg bg-lore-purple/10 flex items-center justify-center text-xs text-lore-purple uppercase font-bold shrink-0">
                    {f.file_type}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{f.filename}</p>
                    <p className="text-xs text-lore-text-muted">
                      {f.source_tag || "No tag"} ·{" "}
                      {f.period_start
                        ? `${f.period_start.slice(0, 7)}`
                        : "No period"}{" "}
                      ·{" "}
                      {f.uploaded_at
                        ? new Date(f.uploaded_at).toLocaleDateString()
                        : ""}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(f.id)}
                    className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
