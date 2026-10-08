export interface VoiceProfile {
  id: string;
  name: string;
  created_at: string;
  ready: boolean;
  duration_seconds: number | null;
  is_preset?: boolean;
  gender?: "male" | "female";
  category?: string;
  style?: string;
  description?: string;
  engine?: string;
  tags?: string[];
  preview_text?: string;
}

