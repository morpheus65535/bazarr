import React from "react";
import { Form, Dropdown, Button } from "react-bootstrap";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheck } from "@fortawesome/free-solid-svg-icons";
import { throttle } from "lodash";

interface DropdownProps {
  title: string;
  className?: string;
  languages: Language[];
  onChanged?: (lang: Language[]) => void;
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

  onBtnSelect(event: React.MouseEvent, lang: Language) {
    event.preventDefault();

    const { languages } = this.props;

    // TODO: Opti with memo
    const enabled = languages.filter((val) => Boolean(val.enabled) === true);

    if (this.props.onChanged) {
      this.props.onChanged(enabled.concat(lang));
    }
  }

  itemList(): JSX.Element {
    const { languages } = this.props;
    const { filter } = this.state;

    const items: JSX.Element[] = languages
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
    const { title, className } = this.props;

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
