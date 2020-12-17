import React from "react";
import { connect } from "react-redux";
import { Button, Container, Row, Col, Form } from "react-bootstrap";

import BasicModal, { ModalProps } from "./BasicModal";

import LanguageSelector from "../LanguageSelector";

interface EditorProps {
  languages: ExtendLanguage[];
  item?: ExtendItem;
  onSubmit?: (form: ItemModifyForm) => void;
}

interface State {
  changed: boolean;
  enabled: ExtendLanguage[];
  hi: boolean;
  forced: boolean;
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.enabledLanguage,
  };
}

const colTitleClass = "text-right my-a";
const rowClass = "py-2";
const colSize = 3;

class Editor extends React.Component<EditorProps & ModalProps, State> {
  constructor(props: EditorProps & ModalProps) {
    super(props);

    this.state = {
      enabled:
        props.item?.languages.map((val) => {
          return {
            ...val,
            enabled: true,
          };
        }) ?? [],
      hi: props.item?.hearing_impaired ?? false,
      forced: props.item?.forced ?? false,
      changed: false,
    };
  }

  updateState<K extends keyof State>(key: K, value: State[K]) {
    let state: State = {
      ...this.state,
      changed: true,
    };
    state[key] = value;
    this.setState(state);
  }

  render() {
    const { item, languages, onSubmit } = this.props;

    const { changed, enabled, hi, forced } = this.state;

    const footer = (
      <Button
        disabled={!changed}
        onClick={(e) => {
          e.preventDefault();
          onSubmit &&
            onSubmit({
              languages: enabled.map((val) => val.code2 ?? ""),
              hi,
              forced,
            });
        }}
      >
        Save
      </Button>
    );

    return (
      <BasicModal {...this.props} footer={footer}>
        <Container fluid>
          <Row className={rowClass}>
            <Col sm={colSize} className={colTitleClass}>
              Audio
            </Col>
            <Col>{item?.audio_language.name}</Col>
          </Row>
          <Row className={rowClass}>
            <Col sm={colSize} className={colTitleClass}>
              Languages
            </Col>
            <Col>
              <LanguageSelector
                avaliable={languages}
                defaultSelect={enabled}
                onChange={(val) => this.updateState("enabled", val)}
              ></LanguageSelector>
            </Col>
          </Row>
          <Row className={rowClass}>
            <Col sm={colSize} className={colTitleClass}>
              HI
            </Col>
            <Col>
              <Form.Check
                type="checkbox"
                defaultChecked={hi}
                onChange={(e) => {
                  this.updateState("hi", e.currentTarget.checked);
                }}
              ></Form.Check>
            </Col>
          </Row>
          <Row className={rowClass}>
            <Col sm={colSize} className={colTitleClass}>
              Forced
            </Col>
            <Col>
              <Form.Check
                type="checkbox"
                defaultChecked={forced}
                onChange={(e) => {
                  this.updateState("forced", e.currentTarget.checked);
                }}
              ></Form.Check>
            </Col>
          </Row>
        </Container>
      </BasicModal>
    );
  }
}

export default connect(mapStateToProps)(Editor);
