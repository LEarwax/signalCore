// Types matching FastAPI response schemas

export interface Engineer {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface Project {
  id: string;
  engineer_id: string;
  name: string;
  address: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AHJProfile {
  name: string;
  abbreviation: string;
  jurisdiction: string;
  state: string;
  min_signal_dbm: number;
  coverage_pct: number;
  freq_bands: string[];
  battery_hours: number;
  special_requirements: string[];
  codes: string[];
  confidence: "exact" | "county" | "default";
}

export interface SubmittalPacket {
  id: string;
  project_id: string;
  ahj_name: string | null;
  ahj_abbreviation: string | null;
  freq_bands: string[] | null;
  engine_type: string | null;
  floor_count: number | null;
  occupancy_type: string | null;
  antenna_count: number | null;
  coverage_pct: number | null;
  status: "pending" | "processing" | "complete" | "failed";
  packet_s3_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface ShareableLink {
  id: string;
  packet_id: string;
  token: string;
  snapshot_data: Record<string, unknown> | null;
  created_at: string;
}
