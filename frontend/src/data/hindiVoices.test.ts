import { describe, expect, it } from "vitest";
import { HINDI_VOICES, HINDI_CATEGORIES } from "./hindiVoices";

describe("100 Hindi Voice Profiles Catalog", () => {
  it("contains exactly 100 professional Hindi voice profiles", () => {
    expect(HINDI_VOICES).toHaveLength(100);
  });

  it("ensures every voice has a unique ID and non-empty metadata", () => {
    const ids = new Set<string>();
    HINDI_VOICES.forEach((voice) => {
      expect(voice.id).toBeTruthy();
      expect(ids.has(voice.id)).toBe(false);
      ids.add(voice.id);

      expect(voice.name).toBeTruthy();
      expect(["male", "female"]).toContain(voice.gender);
      expect(voice.category).toBeTruthy();
      expect(voice.style).toBeTruthy();
      expect(voice.description).toBeTruthy();
      expect(voice.preview_text).toBeTruthy();
      expect(voice.base_speaker).toBeTruthy();
    });
  });

  it("has valid categories mapped in HINDI_CATEGORIES", () => {
    HINDI_VOICES.forEach((voice) => {
      expect(HINDI_CATEGORIES).toContain(voice.category);
    });
  });
});
