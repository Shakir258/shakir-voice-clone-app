interface Props {
  src: string;
  downloadName?: string;
}

export function AudioPlayer({ src, downloadName }: Props) {
  return (
    <div className="audio-player">
      <audio controls src={src} />
      <a className="btn btn-secondary" href={src} download={downloadName ?? true}>
        ⬇ Download
      </a>
    </div>
  );
}
