import React, { FunctionComponent } from "react";
import { Form, InputGroup } from "react-bootstrap";

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

type FixElement = string | (() => JSX.Element);

export interface TextProps extends BasicInput<string | number> {
  placeholder?: string | number;
  password?: boolean;
  prefix?: FixElement;
  postfix?: FixElement;
}

export const Text: FunctionComponent<TextProps> = ({
  placeholder,
  prefix,
  postfix,
  disabled,
  defaultValue,
  password,
  onChange,
}) => {
  if (defaultValue === placeholder) {
    defaultValue = undefined;
  }

  function create(ele: FixElement) {
    if (typeof ele === "string") {
      return <InputGroup.Text>{ele}</InputGroup.Text>;
    } else {
      return ele();
    }
  }

  return (
    <InputGroup>
      {prefix && <InputGroup.Prepend>{create(prefix)}</InputGroup.Prepend>}
      <Form.Control
        type={password ? "password" : "text"}
        placeholder={placeholder?.toString()}
        disabled={disabled}
        defaultValue={defaultValue}
        onChange={(e) => {
          onChange && onChange(e.currentTarget.value);
        }}
      ></Form.Control>
      {postfix && <InputGroup.Append>{create(postfix)}</InputGroup.Append>}
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

export { Selector } from "../../Components";

interface SliderProps {}

export const Slider: FunctionComponent<SliderProps> = (props) => {
  return <Form.Control type="range" className="py-1"></Form.Control>;
};
