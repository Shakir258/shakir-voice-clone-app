export interface GenerationRecord {
  id: string;
  voice_id: string;
  voice_name: string;
  created_at: string;
  text_preview: string;
  full_text_chars: number;
  audio_url: string;
  duration_seconds: number | null;
  chunk_count: number;
}
