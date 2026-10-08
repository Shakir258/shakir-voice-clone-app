import { useEffect, useRef, useState } from "react";

interface Props {
  onReady: (blob: Blob, filename: string) => void;
}

type Mode = "idle" | "recording" | "recorded";

// Browsers record with MediaRecorder in whatever codec they support —
// almost always audio/webm with Opus. That's fine: the backend converts
// it to a model-compatible WAV with ffmpeg (see audio_service.py). We
// don't try to produce WAV in the browser.
function pickMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c)) return c;
  }
  return "";
}

export function VoiceRecorder({ onReady }: Props) {
  const [mode, setMode] = useState<Mode>("idle");
  const [seconds, setSeconds] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const blobRef = useRef<Blob | null>(null);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (timerRef.current) clearInterval(timerRef.current);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
        blobRef.current = blob;
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
        setMode("recorded");
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setSeconds(0);
      setMode("recording");
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch {
      setError(
        "Microphone access was denied or unavailable. Allow microphone " +
          "permission for this site, or upload a recording instead."
      );
    }
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
  }

  function reRecord() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    blobRef.current = null;
    setMode("idle");
  }

  function confirmRecording() {
    if (blobRef.current) {
      onReady(blobRef.current, "recording.webm");
    }
  }

  function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    blobRef.current = file;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
    setMode("recorded");
  }

  return (
    <div className="voice-recorder">
      {error && <div className="error-message">{error}</div>}

      {mode === "idle" && (
        <div className="recorder-controls">
          <button className="btn btn-primary" onClick={startRecording}>
            🎙 Start recording
          </button>
          <span className="or-divider">or</span>
          <label className="btn btn-secondary">
            Upload a file
            <input
              type="file"
              accept="audio/*"
              onChange={handleUpload}
              style={{ display: "none" }}
            />
          </label>
        </div>
      )}

      {mode === "recording" && (
        <div className="recorder-controls">
          <span className="recording-dot" /> Recording… {seconds}s
          <button className="btn btn-danger" onClick={stopRecording}>
            Stop
          </button>
        </div>
      )}

      {mode === "recorded" && previewUrl && (
        <div className="recorder-preview">
          <audio controls src={previewUrl} />
          <div className="recorder-controls">
            <button className="btn btn-secondary" onClick={reRecord}>
              Re-record
            </button>
            <button className="btn btn-primary" onClick={confirmRecording}>
              Use this recording
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
