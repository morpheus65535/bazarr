import { useState } from "react";
import {
  Alert,
  Button,
  Checkbox,
  Group,
  Modal,
  Stack,
  Text,
} from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { faCircleInfo } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { UseMutationResult } from "@tanstack/react-query";
import { notification } from "@/modules/task";

export interface SearchMissingConfig {
  // Receives the ids of the selected items.
  mutation: UseMutationResult<void, unknown, FormType.SearchMissing>;
  // Shows a "Use Whisper fallback" checkbox (checked by default). Only for
  // media whose search can use it, and only when it is enabled in the settings.
  whisperFallbackOption?: boolean;
  // What one selected item is, e.g. "series" / "movie".
  unit: { singular: string; plural: string };
}

interface Props {
  opened: boolean;
  onClose: () => void;
  ids: number[];
  config: SearchMissingConfig;
}

const SearchMissingModal = ({ opened, onClose, ids, config }: Props) => {
  const { mutation, unit, whisperFallbackOption } = config;
  const [starting, setStarting] = useState(false);
  const [whisperFallback, setWhisperFallback] = useState(true);

  const close = () => {
    setWhisperFallback(true);
    onClose();
  };

  const count = ids.length;
  const label = `${count} ${count === 1 ? unit.singular : unit.plural}`;

  const start = async () => {
    setStarting(true);
    try {
      await mutation.mutateAsync(
        whisperFallbackOption ? { ids, whisperFallback } : { ids },
      );
      showNotification(
        notification.info(
          "Search Started",
          `Searching for missing subtitles for ${label}`,
        ),
      );
      close();
    } catch {
      // The API client's response interceptor already reports the error.
    } finally {
      setStarting(false);
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={close}
      title="Search missing subtitles"
      centered
    >
      <Stack gap="md">
        <Text size="sm">
          A search for missing subtitles will be performed for{" "}
          <strong>{label}</strong> selected, across all pages of results if you
          selected them with &quot;Select all matching filters&quot;.
        </Text>

        {whisperFallbackOption && (
          <Checkbox
            checked={whisperFallback}
            onChange={(e) => setWhisperFallback(e.currentTarget.checked)}
            disabled={starting}
            label="Use Whisper fallback for this batch"
            description="Enabled in your settings. Uncheck to skip it for this batch only."
          />
        )}

        <Alert
          color="blue"
          variant="light"
          icon={<FontAwesomeIcon icon={faCircleInfo} />}
          title="Runs as a single task"
        >
          The search runs as one task in the Jobs Manager, working through the
          selected items one at a time. You can cancel the task there at any
          time.
        </Alert>

        <Group justify="flex-end">
          <Button variant="default" onClick={close} disabled={starting}>
            Cancel
          </Button>
          <Button onClick={start} loading={starting} disabled={count === 0}>
            {`Search ${label}`}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
};

export default SearchMissingModal;
