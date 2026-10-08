import type { GenerationRecord } from "../types/generation";
import { apiUrl } from "../services/api";
import { AudioPlayer } from "./AudioPlayer";

interface Props {
  generations: GenerationRecord[];
  onDelete: (id: string) => void;
}

export function GenerationHistory({ generations, onDelete }: Props) {
  if (generations.length === 0) {
    return <p className="empty-hint">No generations yet.</p>;
  }
  return (
    <ul className="generation-history">
      {generations.map((g) => (
        <li key={g.id} className="generation-item">
          <div className="generation-item-header">
            <strong>{g.voice_name}</strong>
            <span className="generation-date">{new Date(g.created_at).toLocaleString()}</span>
          </div>
          <p className="generation-preview">"{g.text_preview}"</p>
          <AudioPlayer src={apiUrl(g.audio_url)} downloadName={`${g.id}.wav`} />
          <button className="btn btn-link" onClick={() => onDelete(g.id)}>
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}
