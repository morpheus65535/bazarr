import React, { FunctionComponent } from "react";
import { Form, InputGroup } from "react-bootstrap";

import { Selector, SelectorProps } from "../../Components";

interface BasicInput<T> {
  disabled?: boolean;
  defaultValue?: T;
  onChange?: (val: T) => void;
}

interface TextProps extends BasicInput<string | number> {
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

interface CheckProps extends BasicInput<boolean> {
  label?: string;
}

export const Check: FunctionComponent<CheckProps> = ({
  label,
  disabled,
  defaultValue,
}) => {
  return (
    <Form.Check
      type="checkbox"
      label={label}
      onChange={() => {}}
      disabled={disabled}
      defaultChecked={defaultValue}
    ></Form.Check>
  );
};

type SelectProps = SelectorProps & BasicInput<string>;

export const Select: FunctionComponent<SelectProps> = (props) => {
  return <Selector {...props}></Selector>;
};
