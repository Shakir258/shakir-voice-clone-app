import { apiDelete, apiGet, apiPost } from "./api";
import type { GenerationRecord } from "../types/generation";

export async function generateSpeech(
  voiceId: string,
  text: string,
  speed: number = 1.0,
  pitch: number = 0.0,
  format: string = "wav"
): Promise<GenerationRecord> {
  return apiPost<GenerationRecord>(`/api/voices/${voiceId}/generate`, { text, speed, pitch, format });
}

export async function listGenerations(): Promise<GenerationRecord[]> {
  const data = await apiGet<{ generations: GenerationRecord[] }>("/api/generations");
  return data.generations;
}

export async function deleteGeneration(id: string): Promise<void> {
  return apiDelete(`/api/generations/${id}`);
}
