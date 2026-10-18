import { FunctionComponent } from "react";
import { Select, Stack, Text } from "@mantine/core";
import { faBullseye, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
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
  isCutoff: boolean;
  error?: string;
  condition?: string;
  onChange: (patch: Partial<Language.ProfileItem>) => void;
  onRemove: () => void;
  onToggleCutoff?: () => void;
}

const LanguageRequirementRow: FunctionComponent<
  LanguageRequirementRowProps
> = ({
  condition,
  error,
  isCutoff,
  item,
  languageData,
  languageName,
  onChange,
  onRemove,
  onToggleCutoff,
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
          {onToggleCutoff && (
            <Action
              label={
                isCutoff
                  ? `Stop searching after ${languageName}`
                  : `Stop searching when ${languageName} is found`
              }
              icon={faBullseye}
              className={styles.touchAction}
              variant={isCutoff ? "filled" : "subtle"}
              color={isCutoff ? "brand" : "secondary"}
              onClick={onToggleCutoff}
            ></Action>
          )}
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
      {isCutoff && (
        <Text size="xs" className={styles.cutoffHint}>
          <FontAwesomeIcon icon={faBullseye} />
          Stops searching once this language is found.
        </Text>
      )}
    </Stack>
  );
};

export default LanguageRequirementRow;
