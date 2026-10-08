import { useState } from "react";
import { generateSpeech } from "../services/generationApi";
import type { GenerationRecord } from "../types/generation";

export function useGeneration() {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerationRecord | null>(null);

  async function generate(
    voiceId: string,
    text: string,
    speed: number = 1.0,
    pitch: number = 0.0,
    format: string = "wav"
  ) {
    setGenerating(true);
    setError(null);
    try {
      const record = await generateSpeech(voiceId, text, speed, pitch, format);
      setResult(record);
      return record;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speech generation failed.");
      return null;
    } finally {
      setGenerating(false);
    }
  }

  return { generate, generating, error, result };
}
