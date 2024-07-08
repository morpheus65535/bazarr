import { FunctionComponent } from "react";
import { Group, Stack, Text } from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";
import {
  faArrowUp,
  faFileCirclePlus,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import styles from "./DropContent.module.scss";

export const DropContent: FunctionComponent = () => {
  return (
    <Group justify="center" gap="xl" className={styles.container}>
      <Dropzone.Idle>
        <FontAwesomeIcon icon={faFileCirclePlus} size="2x" />
      </Dropzone.Idle>
      <Dropzone.Accept>
        <FontAwesomeIcon icon={faArrowUp} size="2x" />
      </Dropzone.Accept>
      <Dropzone.Reject>
        <FontAwesomeIcon icon={faXmark} size="2x" />
      </Dropzone.Reject>
      <Stack gap={0}>
        <Text size="lg">Upload Subtitles</Text>
        <Text c="dimmed" size="sm">
          Attach as many files as you like, you will need to select file
          metadata before uploading
        </Text>
      </Stack>
    </Group>
  );
};
