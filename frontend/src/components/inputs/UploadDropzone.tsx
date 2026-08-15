import { FunctionComponent, RefObject } from "react";
import { Dropzone } from "@mantine/dropzone";
import { DropContent } from "./DropContent";
import styles from "./DropContent.module.scss";

interface UploadDropzoneProps {
  openRef: RefObject<VoidFunction | null>;
  active: boolean;
  onDrop: (files: File[]) => void;
}

export const UploadDropzone: FunctionComponent<UploadDropzoneProps> = ({
  openRef,
  active,
  onDrop,
}) => {
  return (
    <Dropzone.FullScreen
      openRef={openRef}
      active={active}
      onDrop={onDrop}
      classNames={{ inner: styles.dropzoneInner }}
    >
      <DropContent></DropContent>
    </Dropzone.FullScreen>
  );
};
