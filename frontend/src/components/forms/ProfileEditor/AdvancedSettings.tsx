import { FunctionComponent, useMemo } from "react";
import {
  Accordion,
  Badge,
  Group,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import ChipInput from "@/components/inputs/ChipInput";

export interface AdvancedSettingsProps {
  tag: string | undefined;
  mustContain: string[];
  mustNotContain: string[];
  originalFormat: boolean;
  tagError?: string;
  onTagChange: (tag: string | undefined) => void;
  onMustContainChange: (values: string[]) => void;
  onMustNotContainChange: (values: string[]) => void;
  onOriginalFormatChange: (value: boolean) => void;
}

const normalizeTag = (value: string): string =>
  value.toLowerCase().trim().replace(/\s+/g, "_");

const AdvancedSettings: FunctionComponent<AdvancedSettingsProps> = ({
  mustContain,
  mustNotContain,
  onMustContainChange,
  onMustNotContainChange,
  onOriginalFormatChange,
  onTagChange,
  originalFormat,
  tag,
  tagError,
}) => {
  const activeSummary = useMemo(() => {
    const parts: string[] = [];

    if (tag) {
      parts.push("tag");
    }

    if (mustContain.length > 0) {
      parts.push("must contain");
    }

    if (mustNotContain.length > 0) {
      parts.push("must not contain");
    }

    if (originalFormat) {
      parts.push("original format");
    }

    return parts.join(", ");
  }, [mustContain, mustNotContain, originalFormat, tag]);

  const activeCount =
    activeSummary.length > 0 ? activeSummary.split(", ").length : 0;

  return (
    <Accordion variant="separated" chevronPosition="right">
      <Accordion.Item value="advanced">
        <Accordion.Control>
          <Stack gap={2}>
            <Group gap="xs" wrap="nowrap">
              <Text fw={600}>Advanced settings</Text>
              <Badge size="xs" variant="light" color="secondary">
                {activeCount} configured
              </Badge>
            </Group>
            {activeSummary.length > 0 && (
              <Text size="xs" c="dimmed">
                {activeSummary}
              </Text>
            )}
          </Stack>
        </Accordion.Control>
        <Accordion.Panel>
          <Stack gap="sm">
            <TextInput
              id="profile-tag"
              label="Tag"
              placeholder="Optional tag"
              value={tag ?? ""}
              error={tagError}
              onChange={(event) =>
                onTagChange(event.currentTarget.value || undefined)
              }
              onBlur={(event) =>
                onTagChange(
                  normalizeTag(event.currentTarget.value) || undefined,
                )
              }
            ></TextInput>
            <Text size="sm" c="dimmed">
              Used to assign this profile automatically from Sonarr/Radarr tags.
            </Text>
            <ChipInput
              label="Must contain"
              value={mustContain}
              onChange={onMustContainChange}
            ></ChipInput>
            <Text size="sm" c="dimmed">
              Subtitles release info must include one of those words or they
              will be excluded from search results (regex supported).
            </Text>
            <ChipInput
              label="Must not contain"
              value={mustNotContain}
              onChange={onMustNotContainChange}
            ></ChipInput>
            <Text size="sm" c="dimmed">
              Subtitles release info including one of those words (case
              insensitive) will be excluded from search results (regex
              supported).
            </Text>
            <Switch
              label="Use original format"
              checked={originalFormat}
              onChange={(event) =>
                onOriginalFormatChange(event.currentTarget.checked)
              }
            ></Switch>
            <Text size="sm" c="dimmed">
              Download subtitle file without format conversion.
            </Text>
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
};

export default AdvancedSettings;
