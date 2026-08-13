import { useMemo } from "react";
import { useLanguages } from "@/apis/hooks";
import { languageEqualsKey } from "@/pages/Settings/keys";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";

interface GenericEqualTarget<T> {
  content: T;
  hi: boolean;
  forced: boolean;
}

interface LanguageEqualGenericData<T> {
  source: GenericEqualTarget<T>;
  target: GenericEqualTarget<T>;
}

export type LanguageEqualImmediateData =
  LanguageEqualGenericData<Language.CodeType>;

export type LanguageEqualData = LanguageEqualGenericData<Language.Server>;

const decodeEqualTarget = (
  text: string,
): GenericEqualTarget<Language.CodeType> | undefined => {
  const [code, decoration] = text.split("@");

  if (code.length === 0) {
    return undefined;
  }

  const forced = decoration === "forced";
  const hi = decoration === "hi";

  return {
    content: code,
    forced,
    hi,
  };
};

export const decodeEqualData = (
  text: string,
): LanguageEqualImmediateData | undefined => {
  const [first, second] = text.split(":");

  const source = decodeEqualTarget(first);
  const target = decodeEqualTarget(second);

  if (source === undefined || target === undefined) {
    return undefined;
  }

  return {
    source,
    target,
  };
};

const encodeEqualTarget = (
  data: GenericEqualTarget<Language.Server>,
): string => {
  const text =
    data.content.code3 + (data.hi ? "@hi" : data.forced ? "@forced" : "");

  return text;
};

export const encodeEqualData = (data: LanguageEqualData): string => {
  const source = encodeEqualTarget(data.source);
  const target = encodeEqualTarget(data.target);

  return `${source}:${target}`;
};

export const useLatestLanguageEquals = (): LanguageEqualData[] => {
  const { data } = useLanguages();

  const latest = useSettingValue<string[]>(languageEqualsKey);

  return useMemo(
    () =>
      latest
        ?.map(decodeEqualData)
        .map((parsed) => {
          if (parsed === undefined) {
            return undefined;
          }

          const source = data?.find(
            (value) => value.code3 === parsed.source.content,
          );
          const target = data?.find(
            (value) => value.code3 === parsed.target.content,
          );

          if (source === undefined || target === undefined) {
            return undefined;
          }

          return {
            source: { ...parsed.source, content: source },
            target: { ...parsed.target, content: target },
          };
        })
        .filter((v): v is LanguageEqualData => v !== undefined) ?? [],
    [data, latest],
  );
};
