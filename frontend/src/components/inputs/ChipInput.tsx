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
  // TODO: Replace with our own custom implementation instead of just using the
  //       built-in TagsInput. https://mantine.dev/combobox/?e=MultiSelectCreatable
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
