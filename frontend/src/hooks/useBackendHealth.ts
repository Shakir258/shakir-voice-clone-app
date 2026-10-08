import { useEffect, useState } from "react";
import { apiGet } from "../services/api";
import type { ModelStatus } from "../types/api";

const POLL_MS = 4000;

export function useBackendHealth() {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [unreachable, setUnreachable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const data = await apiGet<ModelStatus>("/api/model/status");
        if (!cancelled) {
          setStatus(data);
          setUnreachable(false);
        }
      } catch {
        if (!cancelled) setUnreachable(true);
      } finally {
        if (!cancelled) {
          // Stop polling once the model is ready or has errored — no
          // point hammering the endpoint after the state is settled.
          const settled = status?.status === "ready" || status?.status === "error";
          if (!settled) {
            timer = setTimeout(poll, POLL_MS);
          }
        }
      }
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.status]);

  return { status, unreachable };
}
