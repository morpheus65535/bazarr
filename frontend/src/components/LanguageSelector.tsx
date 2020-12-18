import React, {
  ChangeEvent,
  MouseEvent,
  FunctionComponent,
  useState,
  useMemo,
} from "react";
import { Form, Dropdown, Button, DropdownProps } from "react-bootstrap";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheck } from "@fortawesome/free-solid-svg-icons";

interface Props {
  className?: string;
  avaliable: ExtendLanguage[];
  defaultSelect: ExtendLanguage[];
  onChange?: (lang: ExtendLanguage[]) => void;
}

const LanguageSelector: FunctionComponent<Props> = (props) => {
  const { className, avaliable, defaultSelect, onChange } = props;
  const [filter, setFilter] = useState<string>("");
  const [enabled, setEnabled] = useState<ExtendLanguage[]>(defaultSelect);

  const items = useMemo(
    () =>
      avaliable
        .map((lang) => {
          return {
            ...lang,
            enabled: enabled.some((val) => val.name === lang.name),
          };
        })
        .filter((val) => val.name.includes(filter))
        .map((lang) => (
          <Dropdown.Item
            as="button"
            value={lang.code2}
            key={lang.name}
            className="py-2 d-flex justify-content-between align-items-center"
            onClick={(e: MouseEvent<any>) => {
              e.preventDefault();
              if (lang.enabled) {
                const result = enabled.filter((val) => val.name !== lang.name);
                setEnabled(result);
                onChange && onChange(result);
              } else {
                const result = enabled.concat(lang);
                setEnabled(result);
                onChange && onChange(result);
              }
            }}
          >
            <span>{lang.name}</span>
            {lang.enabled && <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>}
          </Dropdown.Item>
        )),
    [avaliable, enabled, filter, onChange]
  );

  const title = useMemo(() => {
    let name = enabled.map((lang) => lang.name).join(", ");
    if (name.length === 0) {
      name = "Nothing Selected";
    }
    return name;
  }, [enabled]);

  return (
    <Dropdown className={className}>
      <Dropdown.Toggle as={Button} variant="outline-secondary" block className="text-left">
        <span>{title}</span>
      </Dropdown.Toggle>
      <Dropdown.Menu>
        <Dropdown.Header>
          {items.length === 0 ? (
            "No Selectable Items"
          ) : (
            <Form.Control
              type="text"
              placeholder="Filter"
              onChange={(e: ChangeEvent<any>) => {
                setFilter(e.target.value);
              }}
            ></Form.Control>
          )}
        </Dropdown.Header>
        <div
          style={{
            maxHeight: 256,
            maxWidth: 320,
            overflowY: "scroll",
          }}
        >
          {items}
        </div>
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default LanguageSelector;
