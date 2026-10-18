import { FunctionComponent, useMemo } from "react";
import { Alert, Select, Stack, Text } from "@mantine/core";
import { anyCutoff } from "@/components/forms/profileOptions";
import {
  describeGroupLanguages,
  describeLanguage,
} from "@/utilities/languageProfileSummary";
import { LanguageNameResolver } from "@/utilities/languages";

export interface SearchCompletionProps {
  isEnhanced: boolean;
  cutoff: number | null;
  groups: readonly Language.EnhancedGroup[];
  items: readonly Language.ProfileItem[];
  resolveLanguageName: LanguageNameResolver;
  onChange: (cutoff: number | null) => void;
  notice: string | null;
  onDismissNotice: () => void;
}

const noCutoffValue = "none";

const SearchCompletion: FunctionComponent<SearchCompletionProps> = ({
  cutoff,
  groups,
  isEnhanced,
  items,
  notice,
  onChange,
  onDismissNotice,
  resolveLanguageName,
}) => {
  const options = useMemo(() => {
    const result = [
      {
        value: noCutoffValue,
        label: "Keep searching for all unmet requirements",
      },
    ];

    if (isEnhanced) {
      result.push({
        value: String(anyCutoff),
        label: "When any requirement is satisfied",
      });

      for (const group of groups) {
        result.push({
          value: String(group.id),
          label: `When ${describeGroupLanguages(group, resolveLanguageName)} is satisfied`,
        });
      }

      return result;
    }

    result.push({
      value: String(anyCutoff),
      label: "When any of these languages is found",
    });

    for (const item of items) {
      result.push({
        value: String(item.id),
        label: `When ${describeLanguage(item, resolveLanguageName)} is found`,
      });
    }

    return result;
  }, [groups, isEnhanced, items, resolveLanguageName]);

  return (
    <Stack gap="xs">
      <Select
        label="When should Bazarr stop searching?"
        data={options}
        allowDeselect={false}
        value={cutoff === null ? noCutoffValue : String(cutoff)}
        onChange={(value) =>
          onChange(
            value === null || value === noCutoffValue ? null : Number(value),
          )
        }
      ></Select>
      <Text size="sm" c="dimmed">
        The stopping rule applies to the whole profile. Once it is satisfied,
        Bazarr stops searching for every remaining requirement, not only the
        later ones.
      </Text>
      <Text size="sm" c="dimmed">
        A requirement with an audio condition counts as satisfied when the audio
        track does not match, even without downloading a subtitle.
      </Text>
      {notice && (
        <Alert
          variant="light"
          role="status"
          aria-live="polite"
          withCloseButton
          onClose={onDismissNotice}
        >
          {notice}
        </Alert>
      )}
    </Stack>
  );
};

export default SearchCompletion;
