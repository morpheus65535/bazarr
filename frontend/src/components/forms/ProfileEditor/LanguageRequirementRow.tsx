import { FunctionComponent } from "react";
import { Select, Stack, Text } from "@mantine/core";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { Action } from "@/components";
import {
  inclusionOptions,
  inclusionPatch,
  inclusionValue,
  subtitlesTypeOptions,
  subtitleTypePatch,
  subtitleTypeValue,
} from "@/components/forms/profileOptions";
import styles from "./ProfileEditor.module.scss";

export interface LanguageOption {
  value: string;
  label: string;
}

export interface LanguageRequirementRowProps {
  item: Language.ProfileItem;
  languageData: readonly LanguageOption[];
  languageName: string;
  error?: string;
  condition?: string;
  onChange: (patch: Partial<Language.ProfileItem>) => void;
  onRemove: () => void;
}

const LanguageRequirementRow: FunctionComponent<
  LanguageRequirementRowProps
> = ({
  condition,
  error,
  item,
  languageData,
  languageName,
  onChange,
  onRemove,
}) => {
  return (
    <Stack gap={4}>
      <div className={styles.row}>
        <Select
          id={`profile-language-${item.id}`}
          aria-label="Language"
          searchable
          placeholder="Select a language"
          data={languageData}
          value={item.language.length > 0 ? item.language : null}
          error={error}
          onChange={(value) => onChange({ language: value ?? "" })}
        ></Select>
        <Select
          aria-label="Subtitle type"
          allowDeselect={false}
          data={subtitlesTypeOptions}
          value={subtitleTypeValue(item)}
          onChange={(value) => {
            if (value) {
              onChange(subtitleTypePatch(value));
            }
          }}
        ></Select>
        <Select
          aria-label="Search only when"
          allowDeselect={false}
          data={inclusionOptions}
          value={inclusionValue(item)}
          onChange={(value) => {
            if (value) {
              onChange(inclusionPatch(value));
            }
          }}
        ></Select>
        <div className={styles.rowActions}>
          <Action
            label={`Remove ${languageName}`}
            icon={faTrash}
            c="danger"
            className={styles.touchAction}
            onClick={onRemove}
          ></Action>
        </div>
      </div>
      {condition && (
        <Text size="xs" c="dimmed">
          {condition}
        </Text>
      )}
    </Stack>
  );
};

export default LanguageRequirementRow;
