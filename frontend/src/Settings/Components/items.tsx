import React, { FunctionComponent } from "react";
import { Form, InputGroup } from "react-bootstrap";

import { Selector, SelectorProps } from "../../Components";

export const Message: FunctionComponent<{
  type: "warning" | "info";
}> = ({ type, children }) => {
  const cls = ["pr-4"];
  cls.push(type === "warning" ? "text-warning" : "text-muted");

  return <Form.Text className={cls.join(" ")}>{children}</Form.Text>;
};

export interface BasicInput<T> {
  disabled?: boolean;
  defaultValue?: T;
  onChange?: (val: T) => void;
}

export interface TextProps extends BasicInput<string | number> {
  placeholder?: string | number;
  prefix?: string;
  postfix?: string;
}

export const Text: FunctionComponent<TextProps> = ({
  placeholder,
  prefix,
  postfix,
  disabled,
  defaultValue,
}) => {
  if (defaultValue === placeholder) {
    defaultValue = undefined;
  }
  return (
    <InputGroup>
      {prefix && (
        <InputGroup.Prepend>
          <InputGroup.Text>{prefix}</InputGroup.Text>
        </InputGroup.Prepend>
      )}
      <Form.Control
        type="text"
        placeholder={placeholder?.toString()}
        disabled={disabled}
        defaultValue={defaultValue}
        onChange={() => {}}
      ></Form.Control>
      {postfix && (
        <InputGroup.Append>
          <InputGroup.Text>{postfix}</InputGroup.Text>
        </InputGroup.Append>
      )}
    </InputGroup>
  );
};

export interface CheckProps extends BasicInput<boolean> {
  label?: string;
}

export const Check: FunctionComponent<CheckProps> = ({
  label,
  disabled,
  defaultValue,
  onChange,
}) => {
  return (
    <Form.Check
      type="checkbox"
      label={label}
      onChange={(e) => {
        onChange && onChange(e.currentTarget.checked);
      }}
      disabled={disabled}
      defaultChecked={defaultValue}
    ></Form.Check>
  );
};

type SelectProps = SelectorProps & BasicInput<string>;

export const Select: FunctionComponent<SelectProps> = (props) => {
  return <Selector {...props}></Selector>;
};

interface SliderProps {

}

export const Slider: FunctionComponent<SliderProps> = ({ }) => {
  return <Form.Control type="range" className="py-1"></Form.Control>
}
