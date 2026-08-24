export type LanguageMappingVariant = "standard" | "hi" | "forced";
export type LanguageMappingPurpose =
  "language-alias" | "subtitle-type-fallback" | "advanced-exact";

export interface LanguageMappingEndpoint {
  code: Language.CodeType;
  variant: LanguageMappingVariant;
}

export interface LanguageMappingRule {
  source: LanguageMappingEndpoint;
  target: LanguageMappingEndpoint;
}

export interface RawRuleRef {
  index: number;
  raw: string;
}

export type LanguageMappingUnresolvedReason =
  "invalid-format" | "unknown-source" | "unknown-target" | "unknown-languages";

export type LanguageMappingEntry =
  | {
      kind: "resolved";
      index: number;
      raw: string;
      rule: LanguageMappingRule;
      sourceLanguage: Language.Server;
      targetLanguage: Language.Server;
    }
  | {
      kind: "unresolved";
      index: number;
      raw: string;
      reason: LanguageMappingUnresolvedReason;
      rule?: LanguageMappingRule;
    };

export interface LanguageAliasMember extends RawRuleRef {
  variant: LanguageMappingVariant;
  rule: LanguageMappingRule;
}

export interface LanguageAliasGroup {
  kind: "language-alias";
  index: number;
  sourceLanguage: Language.Server;
  targetLanguage: Language.Server;
  members: LanguageAliasMember[];
}

export type LanguageMappingViewItem = LanguageMappingEntry | LanguageAliasGroup;

export type LanguageMappingValidationCode =
  "self" | "duplicate" | "conflicting-source" | "cycle" | "chain" | "hi-forced";

export interface LanguageMappingValidationError {
  code: LanguageMappingValidationCode;
  message: string;
}

const variants: LanguageMappingVariant[] = ["standard", "hi", "forced"];

const parseEndpoint = (text: string): LanguageMappingEndpoint | undefined => {
  const parts = text.split("@");
  if (parts.length > 2) return undefined;

  const [code, decoration] = parts;
  if (!code || code.trim() !== code || /\s/.test(code)) return undefined;
  if (
    decoration !== undefined &&
    decoration !== "hi" &&
    decoration !== "forced"
  ) {
    return undefined;
  }

  return { code, variant: decoration ?? "standard" };
};

export const parseLanguageMapping = (
  raw: string,
): LanguageMappingRule | undefined => {
  const parts = raw.split(":");
  if (parts.length !== 2) return undefined;

  const source = parseEndpoint(parts[0]);
  const target = parseEndpoint(parts[1]);
  return source && target ? { source, target } : undefined;
};

const encodeEndpoint = (endpoint: LanguageMappingEndpoint): string =>
  endpoint.code +
  (endpoint.variant === "standard" ? "" : `@${endpoint.variant}`);

export const encodeLanguageMapping = (rule: LanguageMappingRule): string =>
  `${encodeEndpoint(rule.source)}:${encodeEndpoint(rule.target)}`;

const findLanguage = (
  languages: readonly Language.Server[],
  code: string,
): Language.Server | undefined =>
  languages.find(
    (language) => language.code3 === code || language.code2 === code,
  );

export const resolveLanguageMappings = (
  rawRules: readonly string[],
  languages: readonly Language.Server[],
): LanguageMappingEntry[] =>
  rawRules.map((raw, index) => {
    const rule = parseLanguageMapping(raw);
    if (!rule) {
      return { kind: "unresolved", index, raw, reason: "invalid-format" };
    }

    const sourceLanguage = findLanguage(languages, rule.source.code);
    const targetLanguage = findLanguage(languages, rule.target.code);
    if (!sourceLanguage || !targetLanguage) {
      const reason =
        !sourceLanguage && !targetLanguage
          ? "unknown-languages"
          : !sourceLanguage
            ? "unknown-source"
            : "unknown-target";
      return { kind: "unresolved", index, raw, reason, rule };
    }

    return {
      kind: "resolved",
      index,
      raw,
      rule,
      sourceLanguage,
      targetLanguage,
    };
  });

export const normalizeLanguageMappingRule = (
  rule: LanguageMappingRule,
  languages: readonly Language.Server[],
): LanguageMappingRule => {
  const normalize = (endpoint: LanguageMappingEndpoint) => ({
    ...endpoint,
    code: findLanguage(languages, endpoint.code)?.code3 ?? endpoint.code,
  });
  return { source: normalize(rule.source), target: normalize(rule.target) };
};

export const endpointKey = (endpoint: LanguageMappingEndpoint): string =>
  `${endpoint.code}@${endpoint.variant}`;

const isHiForcedConversion = (rule: LanguageMappingRule): boolean =>
  (rule.source.variant === "hi" && rule.target.variant === "forced") ||
  (rule.source.variant === "forced" && rule.target.variant === "hi");

export const validateLanguageMapping = (
  candidate: LanguageMappingRule,
  existingRules: readonly LanguageMappingRule[],
  ignoredIndex?: number,
): LanguageMappingValidationError | undefined => {
  const rules = existingRules.filter((_, index) => index !== ignoredIndex);
  const source = endpointKey(candidate.source);
  const target = endpointKey(candidate.target);

  if (source === target) {
    return {
      code: "self",
      message:
        "The source and target are identical, so this mapping would have no effect.",
    };
  }
  if (isHiForcedConversion(candidate)) {
    return {
      code: "hi-forced",
      message:
        "Hearing-impaired subtitles cannot be reclassified directly as forced subtitles, or vice versa.",
    };
  }

  const keyedRules = rules.map((rule) => ({
    source: endpointKey(rule.source),
    target: endpointKey(rule.target),
  }));
  if (
    keyedRules.some((rule) => rule.source === source && rule.target === target)
  ) {
    return { code: "duplicate", message: "This mapping already exists." };
  }
  if (keyedRules.some((rule) => rule.source === source)) {
    return {
      code: "conflicting-source",
      message: "This source already maps to another target.",
    };
  }

  const graph = new Map(keyedRules.map((rule) => [rule.source, rule.target]));
  const reachesSource = (current: string, visited: Set<string>): boolean => {
    if (current === source) return true;
    if (visited.has(current)) return false;
    const next = graph.get(current);
    return next ? reachesSource(next, new Set([...visited, current])) : false;
  };
  if (reachesSource(target, new Set())) {
    return {
      code: "cycle",
      message:
        "This mapping would create a cycle. Language mappings must remain one-way.",
    };
  }
  if (
    keyedRules.some((rule) => rule.target === source || rule.source === target)
  ) {
    return {
      code: "chain",
      message:
        "Mappings cannot be chained because Bazarr only applies one mapping at a time.",
    };
  }
  return undefined;
};

export const getParsedLanguageMappings = (
  rawRules: readonly string[],
): LanguageMappingRule[] =>
  rawRules.flatMap((raw) => {
    const rule = parseLanguageMapping(raw);
    return rule ? [rule] : [];
  });

export const createLanguageAliasRules = (
  sourceCode: string,
  targetCode: string,
): LanguageMappingRule[] =>
  variants.map((variant) => ({
    source: { code: sourceCode, variant },
    target: { code: targetCode, variant },
  }));

export const createSubtitleFallbackRule = (
  code: string,
  sourceVariant: "hi" | "forced",
): LanguageMappingRule => ({
  source: { code, variant: sourceVariant },
  target: { code, variant: "standard" },
});

export const validateLanguageMappingBatch = (
  candidates: readonly LanguageMappingRule[],
  rawRules: readonly string[],
  languages: readonly Language.Server[],
  excludedRefs: readonly RawRuleRef[] = [],
): LanguageMappingValidationError | undefined => {
  const excluded = new Set(excludedRefs.map((ref) => ref.index));
  const retained = rawRules.flatMap((raw, index) => {
    if (excluded.has(index)) return [];
    const rule = parseLanguageMapping(raw);
    return rule ? [normalizeLanguageMappingRule(rule, languages)] : [];
  });

  return candidates.reduce<LanguageMappingValidationError | undefined>(
    (error, candidate, index) =>
      error ??
      validateLanguageMapping(
        normalizeLanguageMappingRule(candidate, languages),
        [
          ...retained,
          ...candidates
            .slice(0, index)
            .map((rule) => normalizeLanguageMappingRule(rule, languages)),
        ],
      ),
    undefined,
  );
};

export const buildLanguageMappingView = (
  rawRules: readonly string[],
  languages: readonly Language.Server[],
): LanguageMappingViewItem[] => {
  const entries = resolveLanguageMappings(rawRules, languages);
  const buckets = new Map<
    string,
    Map<LanguageMappingVariant, LanguageMappingEntry[]>
  >();

  entries.forEach((entry) => {
    if (entry.kind !== "resolved") return;
    const rule = normalizeLanguageMappingRule(entry.rule, languages);
    if (
      rule.source.code === rule.target.code ||
      rule.source.variant !== rule.target.variant
    ) {
      return;
    }
    const key = `${rule.source.code}->${rule.target.code}`;
    const byVariant = buckets.get(key) ?? new Map();
    const variantEntries = byVariant.get(rule.source.variant) ?? [];
    byVariant.set(rule.source.variant, [...variantEntries, entry]);
    buckets.set(key, byVariant);
  });

  const groups = new Map<number, LanguageAliasGroup>();
  const consumed = new Set<number>();
  buckets.forEach((byVariant) => {
    if (!variants.every((variant) => byVariant.get(variant)?.length === 1)) {
      return;
    }
    const members = variants.map((variant) => {
      const entry = byVariant.get(variant)?.[0];
      if (!entry || entry.kind !== "resolved")
        throw new Error("Invalid alias group");
      return {
        index: entry.index,
        raw: entry.raw,
        variant,
        rule: entry.rule,
      };
    });
    const firstIndex = Math.min(...members.map((member) => member.index));
    const firstEntry = entries[firstIndex];
    if (!firstEntry || firstEntry.kind !== "resolved") return;
    groups.set(firstIndex, {
      kind: "language-alias",
      index: firstIndex,
      sourceLanguage: firstEntry.sourceLanguage,
      targetLanguage: firstEntry.targetLanguage,
      members,
    });
    members.forEach((member) => consumed.add(member.index));
  });

  return entries.flatMap<LanguageMappingViewItem>((entry) => {
    const group = groups.get(entry.index);
    if (group) return [group];
    return consumed.has(entry.index) ? [] : [entry];
  });
};

const refsAreCurrent = (
  rawRules: readonly string[],
  refs: readonly RawRuleRef[],
): boolean =>
  new Set(refs.map((ref) => ref.index)).size === refs.length &&
  refs.every((ref) => rawRules[ref.index] === ref.raw);

export const applyRuleSet = (
  rawRules: readonly string[],
  refs: readonly RawRuleRef[],
  encodedRules: readonly string[],
): string[] | undefined => {
  if (!refsAreCurrent(rawRules, refs)) return undefined;
  if (refs.length === 0) return [...rawRules, ...encodedRules];
  if (refs.length !== encodedRules.length) return undefined;

  const next = [...rawRules];
  refs.forEach((ref, index) => {
    next[ref.index] = encodedRules[index];
  });
  return next;
};

export const removeRuleSet = (
  rawRules: readonly string[],
  refs: readonly RawRuleRef[],
): string[] | undefined => {
  if (!refsAreCurrent(rawRules, refs)) return undefined;
  const removed = new Set(refs.map((ref) => ref.index));
  return rawRules.filter((_, index) => !removed.has(index));
};

export const languageMappingVariantLabel = (
  variant: LanguageMappingVariant,
): string => {
  switch (variant) {
    case "hi":
      return "Hearing impaired";
    case "forced":
      return "Forced";
    default:
      return "Standard";
  }
};

export interface LanguageMappingPreset {
  source: string;
  target: string;
  label: string;
}

export const languageMappingPresets: readonly LanguageMappingPreset[] = [
  { source: "spl", target: "spa", label: "Spanish (Latino) → Spanish" },
  { source: "pob", target: "por", label: "Portuguese (Brazil) → Portuguese" },
  { source: "zht", target: "zho", label: "Chinese Traditional → Chinese" },
];
