import { describe, expect, it } from "vitest";
import {
  applyRuleSet,
  buildLanguageMappingView,
  createLanguageAliasRules,
  createSubtitleFallbackRule,
  encodeLanguageMapping,
  flipLanguageMappingRule,
  flipRuleSet,
  getParsedLanguageMappings,
  LanguageMappingRule,
  normalizeLanguageMappingRule,
  parseLanguageMapping,
  removeRuleSet,
  resolveLanguageMappings,
  validateLanguageMapping,
  validateLanguageMappingBatch,
} from "@/pages/Settings/Languages/LanguageMappings/model";

const rule = (
  source: string,
  target: string,
  sourceVariant: LanguageMappingRule["source"]["variant"] = "standard",
  targetVariant: LanguageMappingRule["target"]["variant"] = "standard",
): LanguageMappingRule => ({
  source: { code: source, variant: sourceVariant },
  target: { code: target, variant: targetVariant },
});

const languages: Language.Server[] = [
  { code2: "en", code3: "eng", name: "English", enabled: true },
  { code2: "fr", code3: "fre", name: "French", enabled: true },
  {
    code2: "ea",
    code3: "spl",
    name: "Spanish (Latino)",
    enabled: false,
  },
  { code2: "es", code3: "spa", name: "Spanish", enabled: true },
];

describe("language mapping codec", () => {
  it.each([
    ["spl:spa", rule("spl", "spa")],
    ["eng@hi:eng", rule("eng", "eng", "hi")],
    ["eng:eng@forced", rule("eng", "eng", "standard", "forced")],
    ["spa-MX@forced:spa", rule("spa-MX", "spa", "forced")],
  ])("parses %s", (raw, expected) => {
    expect(parseLanguageMapping(raw)).toEqual(expected);
  });

  it.each([
    "invalid",
    "eng:",
    ":eng",
    "eng:fre:spa",
    "eng@cc:fre",
    "eng@hi@forced:fre",
    " eng:fre",
  ])("rejects malformed value %s", (raw) => {
    expect(parseLanguageMapping(raw)).toBeUndefined();
  });

  it("encodes variants using the existing backend format", () => {
    expect(encodeLanguageMapping(rule("spl", "spa", "hi", "forced"))).toBe(
      "spl@hi:spa@forced",
    );
  });
});

describe("language mapping resolution", () => {
  it("resolves code2 and code3 values", () => {
    const entries = resolveLanguageMappings(["spl:spa", "en:fre"], languages);

    expect(entries[0]).toMatchObject({
      kind: "resolved",
      sourceLanguage: { code3: "spl" },
      targetLanguage: { code3: "spa" },
    });
    expect(entries[1]).toMatchObject({
      kind: "resolved",
      sourceLanguage: { code3: "eng" },
      targetLanguage: { code3: "fre" },
    });
  });

  it("preserves malformed and unavailable raw values in their original order", () => {
    const raw = ["invalid", "unknown:spa", "spl:spa", "eng:missing"];
    const entries = resolveLanguageMappings(raw, languages);

    expect(entries.map((entry) => entry.raw)).toEqual(raw);
    expect(entries.map((entry) => entry.kind)).toEqual([
      "unresolved",
      "unresolved",
      "resolved",
      "unresolved",
    ]);
    expect(entries[0]).toMatchObject({ reason: "invalid-format" });
    expect(entries[1]).toMatchObject({ reason: "unknown-source" });
    expect(entries[3]).toMatchObject({ reason: "unknown-target" });
  });

  it("returns only syntactically valid rules for graph validation", () => {
    expect(getParsedLanguageMappings(["invalid", "eng:fre"])).toEqual([
      rule("eng", "fre"),
    ]);
  });

  it("normalizes code2 rules before conflict validation", () => {
    expect(normalizeLanguageMappingRule(rule("en", "fr"), languages)).toEqual(
      rule("eng", "fre"),
    );
  });
});

describe("language mapping validation", () => {
  it("rejects a mapping to the same endpoint", () => {
    expect(validateLanguageMapping(rule("eng", "eng"), [])?.code).toBe("self");
  });

  it("allows converting HI or Forced to Standard", () => {
    expect(
      validateLanguageMapping(rule("eng", "eng", "hi"), []),
    ).toBeUndefined();
    expect(
      validateLanguageMapping(rule("eng", "eng", "forced"), []),
    ).toBeUndefined();
  });

  it("rejects direct HI and Forced conversions", () => {
    expect(
      validateLanguageMapping(rule("eng", "eng", "hi", "forced"), [])?.code,
    ).toBe("hi-forced");
    expect(
      validateLanguageMapping(rule("eng", "eng", "forced", "hi"), [])?.code,
    ).toBe("hi-forced");
  });

  it("rejects duplicates and conflicting sources", () => {
    expect(
      validateLanguageMapping(rule("eng", "fre"), [rule("eng", "fre")])?.code,
    ).toBe("duplicate");
    expect(
      validateLanguageMapping(rule("eng", "spa"), [rule("eng", "fre")])?.code,
    ).toBe("conflicting-source");
  });

  it("rejects direct and multi-hop cycles", () => {
    expect(
      validateLanguageMapping(rule("fre", "eng"), [rule("eng", "fre")])?.code,
    ).toBe("cycle");
    expect(
      validateLanguageMapping(rule("spa", "eng"), [
        rule("eng", "fre"),
        rule("fre", "spa"),
      ])?.code,
    ).toBe("cycle");
  });

  it("rejects non-cyclic chains", () => {
    expect(
      validateLanguageMapping(rule("fre", "spa"), [rule("eng", "fre")])?.code,
    ).toBe("chain");
    expect(
      validateLanguageMapping(rule("spa", "eng"), [rule("eng", "fre")])?.code,
    ).toBe("chain");
  });

  it("can ignore the mapping currently being edited", () => {
    const existing = [rule("eng", "fre"), rule("spl", "spa")];

    expect(
      validateLanguageMapping(rule("eng", "spa"), existing, 0),
    ).toBeUndefined();
  });
});

describe("conceptual language aliases", () => {
  const aliasRaw = [
    "spl:spa",
    "unresolved-value",
    "spl@forced:spa@forced",
    "spl@hi:spa@hi",
  ];

  it("generates a type-preserving trio", () => {
    expect(
      createLanguageAliasRules("spl", "spa").map(encodeLanguageMapping),
    ).toEqual(["spl:spa", "spl@hi:spa@hi", "spl@forced:spa@forced"]);
    expect(encodeLanguageMapping(createSubtitleFallbackRule("eng", "hi"))).toBe(
      "eng@hi:eng",
    );
  });

  it("groups a complete non-contiguous trio without moving raw values", () => {
    const view = buildLanguageMappingView(aliasRaw, languages);

    expect(view).toHaveLength(2);
    expect(view[0]).toMatchObject({
      kind: "language-alias",
      sourceLanguage: { code3: "spl" },
      targetLanguage: { code3: "spa" },
      members: [{ index: 0 }, { index: 3 }, { index: 2 }],
    });
    expect(view[1]).toMatchObject({
      kind: "unresolved",
      raw: "unresolved-value",
    });
  });

  it("does not group a partial alias", () => {
    expect(
      buildLanguageMappingView(["spl:spa", "spl@hi:spa@hi"], languages).map(
        (entry) => entry.kind,
      ),
    ).toEqual(["resolved", "resolved"]);
  });

  it("edits and removes guarded rules without touching unrelated entries", () => {
    const refs = [
      { index: 0, raw: aliasRaw[0] },
      { index: 3, raw: aliasRaw[3] },
      { index: 2, raw: aliasRaw[2] },
    ];
    expect(
      applyRuleSet(aliasRaw, refs, [
        "eng:spa",
        "eng@hi:spa@hi",
        "eng@forced:spa@forced",
      ]),
    ).toEqual([
      "eng:spa",
      "unresolved-value",
      "eng@forced:spa@forced",
      "eng@hi:spa@hi",
    ]);
    expect(removeRuleSet(aliasRaw, refs)).toEqual(["unresolved-value"]);
  });

  it("rejects stale references and validates batches atomically", () => {
    expect(
      applyRuleSet(aliasRaw, [{ index: 0, raw: "changed" }], ["eng:fre"]),
    ).toBeUndefined();
    expect(
      validateLanguageMappingBatch(
        createLanguageAliasRules("spl", "spa"),
        ["spl:spa"],
        languages,
      )?.code,
    ).toBe("duplicate");
  });
});

describe("flipping language mappings", () => {
  it("reverses endpoints including variants", () => {
    expect(
      encodeLanguageMapping(
        flipLanguageMappingRule(rule("spl", "spa", "forced", "standard")),
      ),
    ).toBe("spa:spl@forced");
  });

  it("flips a single mapping in place", () => {
    expect(flipRuleSet(["eng:fre"], [{ index: 0, raw: "eng:fre" }])).toEqual([
      "fre:eng",
    ]);
  });

  it("flips every member of an alias trio", () => {
    const aliasRaw = ["spl:spa", "spl@hi:spa@hi", "spl@forced:spa@forced"];
    const refs = aliasRaw.map((raw, index) => ({ index, raw }));

    expect(flipRuleSet(aliasRaw, refs)).toEqual([
      "spa:spl",
      "spa@hi:spl@hi",
      "spa@forced:spl@forced",
    ]);
  });

  it("leaves unrelated entries untouched", () => {
    expect(
      flipRuleSet(
        ["eng:fre", "unresolved", "deu:eng"],
        [{ index: 0, raw: "eng:fre" }],
      ),
    ).toEqual(["fre:eng", "unresolved", "deu:eng"]);
  });

  it("rejects stale references and empty refs", () => {
    expect(
      flipRuleSet(["eng:fre"], [{ index: 0, raw: "changed" }]),
    ).toBeUndefined();
    expect(flipRuleSet(["eng:fre"], [])).toBeUndefined();
  });
});
