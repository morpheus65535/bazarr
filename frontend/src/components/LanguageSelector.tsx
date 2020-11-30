import React from "react";
import { Form, Dropdown, Button } from "react-bootstrap";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheck } from "@fortawesome/free-solid-svg-icons";
import { throttle } from "lodash";

interface DropdownProps {
  className?: string;
  languages: ExtendLanguage[];
  enabled: ExtendLanguage[];
  onChanged?: (lang: ExtendLanguage[]) => void;
}

interface DropdownState {
  filter: string;
}

export default class LanguageSelector extends React.Component<
  DropdownProps,
  DropdownState
> {
  constructor(props: DropdownProps) {
    super(props);
    this.state = {
      filter: "",
    };
  }

  updateFilter = throttle((val: string) => {
    this.setState({
      filter: val,
    });
  }, 100);

  onFilterChanged(event: React.ChangeEvent<HTMLTextAreaElement>) {
    const value = event.target.value;
    this.updateFilter(value);
  }

  onBtnSelect(event: React.MouseEvent, lang: ExtendLanguage) {
    event.preventDefault();

    const { enabled } = this.props;

    if (this.props.onChanged) {
      this.props.onChanged(enabled.concat(lang));
    }
  }

  itemList(): JSX.Element {
    const { languages, enabled } = this.props;
    const { filter } = this.state;

    const enabledSet = new Set(enabled.map((lang) => lang.name));

    const enabledAllList = languages.map((lang) => {
      return {
        ...lang,
        enabled: enabledSet.has(lang.name),
      };
    });

    const items: JSX.Element[] = enabledAllList
      .filter((val) => val.name.includes(filter))
      .map((val) => (
        <Dropdown.Item
          as="button"
          value={val.code2}
          key={val.name}
          className="py-2 d-flex justify-content-between"
          onClick={(e: any) => this.onBtnSelect(e, val)}
        >
          <span>{val.name}</span>
          {Boolean(val.enabled) === true && (
            <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>
          )}
        </Dropdown.Item>
      ));

    const itemHolderStyle: React.CSSProperties = {
      maxHeight: 256,
      overflowY: "scroll",
    };

    return (
      <Dropdown.Menu>
        <Dropdown.Header>
          <Form.Control
            type="text"
            placeholder="Filter"
            onChange={this.onFilterChanged.bind(this)}
          ></Form.Control>
        </Dropdown.Header>
        <div style={itemHolderStyle}>{items}</div>
      </Dropdown.Menu>
    );
  }

  render() {
    const { enabled, className } = this.props;

    let title = enabled.map((lang) => lang.name).join(",");
    if (title.length === 0) {
      title = "Nothing Selected";
    }

    return (
      <Dropdown className={className}>
        <Dropdown.Toggle as={Button} variant="outline-secondary">
          <span className="mx-1">{title}</span>
        </Dropdown.Toggle>
        {this.itemList()}
      </Dropdown>
    );
  }
}
