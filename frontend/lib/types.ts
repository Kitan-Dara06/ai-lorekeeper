export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  user_id: string;
  email: string;
}

export interface FileListItem {
  id: string;
  filename: string;
  file_type: string;
  source_tag: string | null;
  period_start: string | null;
  period_end: string | null;
  uploaded_at: string;
  has_extracted_text: boolean;
}

export interface FileListResponse {
  files: FileListItem[];
  total: number;
}

export interface SynthesisRunInfo {
  id: string;
  file_count: number;
  triggered_at: string;
  status: string;
}

export interface SynthesisRunList {
  runs: SynthesisRunInfo[];
  total: number;
}

export interface StoryArc {
  title: string;
  description: string;
}

export interface RecurringPerson {
  identifier: string;
  context: string;
}

export interface DefiningMoment {
  moment: string;
  significance: string;
}

export interface MindsetShift {
  from_state: string;
  to_state: string;
  evidence: string;
  period: string;
}

export interface IdentityContradiction {
  observation: string;
  evidence: string;
  interpretation: string;
}

export interface LoreSnapshot {
  id: string;
  run_id: string;
  the_sentence: string;
  narrative: string;
  story_arcs: StoryArc[];
  recurring_people: RecurringPerson[];
  defining_moments: DefiningMoment[];
  mindset_shifts: MindsetShift[];
  core_themes: string[];
  identity_contradictions: IdentityContradiction[];
  created_at: string;
  run_triggered_at: string;
  file_count: number;
}

export interface LoreSnapshotListItem {
  id: string;
  run_id: string;
  the_sentence: string;
  created_at: string;
  status: string;
}

export interface LoreSnapshotList {
  snapshots: LoreSnapshotListItem[];
  total: number;
}
