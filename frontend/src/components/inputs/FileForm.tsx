import React, {
  ChangeEvent,
  FunctionComponent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Form } from "react-bootstrap";

export interface FileFormProps {
  disabled?: boolean;
  multiple?: boolean;
  emptyText: string;
  files?: File[];
  onChange?: (files: File[]) => void;
}

export const FileForm: FunctionComponent<FileFormProps> = ({
  files,
  emptyText,
  multiple,
  disabled,
  onChange,
}) => {
  const [fileList, setFileList] = useState<File[]>([]);

  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (files) {
      setFileList(files);

      if (files.length === 0 && input.current) {
        // Manual reset file input
        input.current.value = "";
      }
    }
  }, [files]);

  const label = useMemo(() => {
    if (fileList.length === 0) {
      return emptyText;
    } else {
      if (multiple) {
        return `${fileList.length} Files`;
      } else {
        return fileList[0].name;
      }
    }
  }, [fileList, emptyText, multiple]);

  return (
    <Form.File
      disabled={disabled}
      custom
      label={label}
      multiple={multiple}
      ref={input}
      onChange={(e: ChangeEvent<HTMLInputElement>) => {
        const { files } = e.target;
        if (files) {
          const list: File[] = [];
          for (const file of files) {
            list.push(file);
          }
          setFileList(list);
          onChange && onChange(list);
        }
      }}
    ></Form.File>
  );
};
