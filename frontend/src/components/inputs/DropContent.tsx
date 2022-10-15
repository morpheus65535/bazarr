import {
  faArrowUp,
  faFileCirclePlus,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { createStyles, Group, Stack, Text } from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";
import { FunctionComponent } from "react";

const useStyle = createStyles((theme) => {
  return {
    container: {
      pointerEvents: "none",
      minHeight: 220,
    },
  };
});

export const DropContent: FunctionComponent = () => {
  const { classes } = useStyle();

  return (
    <Group position="center" spacing="xl" className={classes.container}>
      <Dropzone.Idle>
        <FontAwesomeIcon icon={faFileCirclePlus} size="2x" />
      </Dropzone.Idle>
      <Dropzone.Accept>
        <FontAwesomeIcon icon={faArrowUp} size="2x" />
      </Dropzone.Accept>
      <Dropzone.Reject>
        <FontAwesomeIcon icon={faXmark} size="2x" />
      </Dropzone.Reject>
      <Stack spacing={0}>
        <Text size="lg">Upload Subtitles</Text>
        <Text color="dimmed" size="sm">
          Attach as many files as you like, you will need to select file
          metadata before uploading
        </Text>
      </Stack>
    </Group>
  );
};
