import { useSelectorOptions } from "@/utilities";
import { FunctionComponent } from "react";
import { MultiSelector, MultiSelectorProps } from "./Selector";

export type ChipInputProps = Omit<
  MultiSelectorProps<string>,
  | "searchable"
  | "creatable"
  | "getCreateLabel"
  | "onCreate"
  | "options"
  | "getkey"
>;

const ChipInput: FunctionComponent<ChipInputProps> = ({ ...props }) => {
  const { value, onChange } = props;

  const options = useSelectorOptions(value ?? [], (v) => v);

  return (
    <MultiSelector
      {...props}
      {...options}
      creatable
      searchable
      getCreateLabel={(query) => `Add "${query}"`}
      onCreate={(query) => {
        onChange?.([...(value ?? []), query]);
        return query;
      }}
    ></MultiSelector>
  );
};

export default ChipInput;
