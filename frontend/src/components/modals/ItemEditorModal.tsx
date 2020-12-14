import React, { FunctionComponent } from "react";
import { connect } from "react-redux";
import { Button, Container, Row, Col, Form } from "react-bootstrap";

import BasicModal, { ModalProps } from "./BasicModal";

import LanguageSelector from "../LanguageSelector";

interface EditorProps {
  languages: ExtendLanguage[];
  item?: ExtendItem;
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.enabledLanguage,
  };
}

const Editor: FunctionComponent<EditorProps & ModalProps> = (props) => {
  const { item, languages } = props;

  const colTitleClass = "text-right my-a";
  const rowClass = "py-2";
  const colSize = 3;

  let enabled: ExtendLanguage[] = [];
  if (item?.languages instanceof Array) {
    enabled = item?.languages.map((lang) => {
      return {
        code2: lang.code2,
        code3: lang.code3,
        enabled: true,
        name: lang.name,
      };
    });
  }

  const footer = <Button>Save</Button>;

  return (
    <BasicModal {...props} footer={footer}>
      <Container fluid>
        <Row className={rowClass}>
          <Col sm={colSize} className={colTitleClass}>
            Audio Profile
          </Col>
          <Col>{item?.audio_language.name}</Col>
        </Row>
        <Row className={rowClass}>
          <Col sm={colSize} className={colTitleClass}>
            Subtitles Language(s)
          </Col>
          <Col>
            {/* TODO: Make it useable */}
            <LanguageSelector
              enabled={enabled}
              languages={languages}
            ></LanguageSelector>
          </Col>
        </Row>
        <Row className={rowClass}>
          <Col sm={colSize} className={colTitleClass}>
            Hearing-Impaired
          </Col>
          <Col>
            <Form.Check
              type="checkbox"
              defaultChecked={item?.hearing_impaired}
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
              defaultChecked={item?.forced}
            ></Form.Check>
          </Col>
        </Row>
      </Container>
    </BasicModal>
  );
};

export default connect(mapStateToProps)(Editor);
