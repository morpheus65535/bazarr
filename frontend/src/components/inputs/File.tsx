import {
  faArrowUp,
  faFileCirclePlus,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, Stack, Text } from "@mantine/core";
import {
  Dropzone,
  DropzoneProps,
  DropzoneStatus,
  FullScreenDropzone,
  FullScreenDropzoneProps,
} from "@mantine/dropzone";
import { FunctionComponent, useMemo } from "react";

export type FileProps = Omit<DropzoneProps, "children"> & {
  inner?: FileInnerComponent;
};

const File: FunctionComponent<FileProps> = ({
  inner: Inner = FileInner,
  ...props
}) => {
  return (
    <Dropzone {...props}>
      {(status) => <Inner status={status}></Inner>}
    </Dropzone>
  );
};

export type FileOverlayProps = Omit<FullScreenDropzoneProps, "children"> & {
  inner?: FileInnerComponent;
};

export const FileOverlay: FunctionComponent<FileOverlayProps> = ({
  inner: Inner = FileInner,
  ...props
}) => {
  return (
    <FullScreenDropzone {...props}>
      {(status) => <Inner status={status}></Inner>}
    </FullScreenDropzone>
  );
};

export type FileInnerProps = {
  status: DropzoneStatus;
};

type FileInnerComponent = FunctionComponent<FileInnerProps>;

const FileInner: FileInnerComponent = ({ status }) => {
  const { accepted, rejected } = status;
  const icon = useMemo(() => {
    if (accepted) {
      return faArrowUp;
    } else if (rejected) {
      return faXmark;
    } else {
      return faFileCirclePlus;
    }
  }, [accepted, rejected]);

  return (
    <Stack m="lg" align="center" spacing="xs" style={{ pointerEvents: "none" }}>
      <Box mb="md">
        <FontAwesomeIcon size="3x" icon={icon}></FontAwesomeIcon>
      </Box>
      <Text size="lg">Upload files here</Text>
      <Text color="dimmed" size="sm">
        Drag and drop, or click to select
      </Text>
    </Stack>
  );
};

export default File;
