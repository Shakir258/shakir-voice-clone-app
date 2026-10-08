import { apiDelete, apiGet, apiPatch, apiPost, apiPostForm } from "./api";
import type { VoiceProfile } from "../types/voice";

export async function listVoices(): Promise<VoiceProfile[]> {
  const data = await apiGet<{ voices: VoiceProfile[] }>("/api/voices");
  return data.voices;
}

export async function createVoice(name: string, audio: Blob, filename: string): Promise<VoiceProfile> {
  const form = new FormData();
  form.append("name", name);
  form.append("file", audio, filename);
  return apiPostForm<VoiceProfile>("/api/voices", form);
}

export async function renameVoice(voiceId: string, name: string): Promise<VoiceProfile> {
  return apiPatch<VoiceProfile>(`/api/voices/${voiceId}`, { name });
}

export async function deleteVoice(voiceId: string): Promise<void> {
  return apiDelete(`/api/voices/${voiceId}`);
}

export async function recomputeVoice(voiceId: string): Promise<VoiceProfile> {
  return apiPost<VoiceProfile>(`/api/voices/${voiceId}/recompute`);
}
