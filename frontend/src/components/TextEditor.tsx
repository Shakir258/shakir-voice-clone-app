interface Props {
  value: string;
  onChange: (value: string) => void;
  maxChars: number;
}

export function TextEditor({ value, onChange, maxChars }: Props) {
  const overLimit = value.length > maxChars;
  return (
    <div className="text-editor">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onPaste={() => {
          /* native paste behavior is fine — no special handling needed */
        }}
        placeholder="Type or paste the text you want spoken in your voice…"
        rows={8}
      />
      <div className="text-editor-footer">
        <span className={overLimit ? "char-count over-limit" : "char-count"}>
          {value.length.toLocaleString()} / {maxChars.toLocaleString()} characters
        </span>
        <button className="btn btn-link" onClick={() => onChange("")} disabled={!value}>
          Clear
        </button>
      </div>
      {overLimit && (
        <p className="error-message">
          Text is over the {maxChars.toLocaleString()}-character limit for one
          generation. Shorten it or split it into multiple generations.
        </p>
      )}
    </div>
  );
}
