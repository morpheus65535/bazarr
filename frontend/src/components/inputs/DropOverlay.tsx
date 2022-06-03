import {
  faArrowUp,
  faFileCirclePlus,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, createStyles, Overlay, Stack, Text } from "@mantine/core";
import clsx from "clsx";
import { FunctionComponent, useMemo } from "react";
import { DropzoneState } from "react-dropzone";

const useStyle = createStyles((theme) => {
  return {
    container: {
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
    },
    inner: {
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      overflow: "hidden",
      margin: theme.spacing.md,
      borderRadius: theme.radius.md,
      borderWidth: "0.2rem",
      borderStyle: "dashed",
      borderColor: theme.colors.gray[7],
      backgroundColor: theme.fn.rgba(theme.colors.gray[0], 0.4),
    },
    accepted: {
      borderColor: theme.colors.brand[7],
      backgroundColor: theme.fn.rgba(theme.colors.brand[0], 0.6),
    },
    rejected: {
      borderColor: theme.colors.red[7],
      backgroundColor: theme.fn.rgba(theme.colors.red[0], 0.9),
    },
  };
});

export interface DropOverlayProps {
  state: DropzoneState;
  zIndex?: number;
}

export const DropOverlay: FunctionComponent<DropOverlayProps> = ({
  state,
  children,
  zIndex = 10,
}) => {
  const {
    getRootProps,
    isDragActive,
    isDragAccept: accepted,
    isDragReject: rejected,
  } = state;

  const { classes } = useStyle();

  const visible = isDragActive;

  const icon = useMemo(() => {
    if (accepted) {
      return faArrowUp;
    } else if (rejected) {
      return faXmark;
    } else {
      return faFileCirclePlus;
    }
  }, [accepted, rejected]);

  const title = useMemo(() => {
    if (accepted) {
      return "Release to Upload";
    } else if (rejected) {
      return "Cannot Upload Files";
    } else {
      return "Upload Subtitles";
    }
  }, [accepted, rejected]);

  const subtitle = useMemo(() => {
    if (accepted) {
      return "";
    } else if (rejected) {
      return "Some files are invalid";
    } else {
      return "Drop to upload";
    }
  }, [accepted, rejected]);

  return (
    <Box sx={{ position: "relative" }} {...getRootProps()}>
      {visible && (
        <Box className={classes.container} style={{ zIndex }}>
          <Stack
            spacing="xs"
            className={clsx(classes.inner, {
              [classes.accepted]: accepted,
              [classes.rejected]: rejected,
            })}
            style={{ zIndex: zIndex + 1 }}
          >
            <Box>
              <FontAwesomeIcon icon={icon} size="3x" />
            </Box>
            <Text size="xl">{title}</Text>
            <Text color="gray" size="sm">
              {subtitle}
            </Text>
          </Stack>
          <Overlay zIndex={zIndex}></Overlay>
        </Box>
      )}
      {children}
    </Box>
  );
};
