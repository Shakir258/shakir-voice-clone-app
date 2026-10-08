import { useCallback, useEffect, useState } from "react";
import { listVoices } from "../services/voiceApi";
import type { VoiceProfile } from "../types/voice";

export function useVoices() {
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setVoices(await listVoices());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load voice profiles.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { voices, loading, error, refresh };
}
