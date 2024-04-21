import { FunctionComponent } from "react";
import { TagsInput } from "@mantine/core";

export interface ChipInputProps {
  defaultValue?: string[] | undefined;
  value?: readonly string[] | null;
  label?: string;
  onChange?: (value: string[]) => void;
}

const ChipInput: FunctionComponent<ChipInputProps> = ({
  defaultValue,
  value,
  label,
  onChange,
}: ChipInputProps) => {
  return (
    <TagsInput
      defaultValue={defaultValue}
      label={label}
      value={value ? value?.map((v) => v) : []}
      onChange={onChange}
      clearable
    ></TagsInput>
  );
};

export default ChipInput;
