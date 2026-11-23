import { FunctionComponent, useMemo } from "react";
import { Alert, Select, Stack, Text } from "@mantine/core";
import { anyCutoff } from "@/components/forms/profileOptions";
import { describeGroupLanguages } from "@/utilities/languageProfileSummary";
import { LanguageNameResolver } from "@/utilities/languages";

export interface SearchCompletionProps {
  cutoff: number | null;
  groups: readonly Language.EnhancedGroup[];
  resolveLanguageName: LanguageNameResolver;
  onChange: (cutoff: number | null) => void;
  notice: string | null;
  onDismissNotice: () => void;
}

const noCutoffValue = "none";

const SearchCompletion: FunctionComponent<SearchCompletionProps> = ({
  cutoff,
  groups,
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
      {
        value: String(anyCutoff),
        label: "When any requirement is satisfied",
      },
    ];

    for (const group of groups) {
      result.push({
        value: String(group.id),
        label: `When ${describeGroupLanguages(group, resolveLanguageName)} is satisfied`,
      });
    }

    return result;
  }, [groups, resolveLanguageName]);

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
