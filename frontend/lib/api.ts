import { supabase } from "./supabase";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {}
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Files
export async function getFiles() {
  return apiFetch<{ files: any[]; total: number }>("/api/files/");
}

export async function uploadFile(
  file: File,
  sourceTag?: string,
  periodStart?: string,
  periodEnd?: string,
) {
  const token = await getAccessToken();
  const formData = new FormData();
  formData.append("file", file);
  if (sourceTag) formData.append("source_tag", sourceTag);
  if (periodStart) formData.append("period_start", periodStart);
  if (periodEnd) formData.append("period_end", periodEnd);

  const res = await fetch(`${API_BASE}/api/files/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export async function deleteFile(fileId: string) {
  return apiFetch<null>(`/api/files/${fileId}`, { method: "DELETE" });
}

// Synthesis
export async function triggerSynthesis(fileIds?: string[]) {
  return apiFetch<{ run_id: string; status: string; message: string }>(
    "/api/synthesis/trigger",
    { method: "POST", body: JSON.stringify({ file_ids: fileIds || null }) },
  );
}

export async function getRuns() {
  return apiFetch<{ runs: any[]; total: number }>("/api/synthesis/runs");
}

export async function getSnapshots() {
  return apiFetch<{ snapshots: any[]; total: number }>(
    "/api/synthesis/snapshots",
  );
}

export async function getSnapshotDetail(loreId: string) {
  return apiFetch<any>(`/api/synthesis/snapshots/${loreId}`);
}

export async function deleteAccount() {
  const data = await apiFetch<null>("/api/auth/account", { method: "DELETE" });
  return data;
}
