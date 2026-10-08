import { useEffect, useState } from "react";
import { GenerationHistory } from "../components/GenerationHistory";
import { LoadingState } from "../components/LoadingState";
import { deleteGeneration, listGenerations } from "../services/generationApi";
import type { GenerationRecord } from "../types/generation";

export function History() {
  const [generations, setGenerations] = useState<GenerationRecord[]>([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setGenerations(await listGenerations());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="page">
      <h1>History</h1>
      {loading ? (
        <LoadingState />
      ) : (
        <GenerationHistory
          generations={generations}
          onDelete={async (id) => {
            await deleteGeneration(id);
            refresh();
          }}
        />
      )}
    </div>
  );
}
