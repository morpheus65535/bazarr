import React, { FunctionComponent } from "react";
import { connect } from "react-redux"
import { Button, Container, Modal, Row, Col, Form } from "react-bootstrap";

import LanguageSelector from "../../components/LanguageSelector";

interface Props {
  languages: Array<Language>;
  series?: Series;
  close?: () => void;
}

function mapStateToProps({ system, series }: StoreState) {
  return {
    languages: system.enabledLanguage,
  };
}

const SeriesEditModal: FunctionComponent<Props> = (props) => {
  const { series, languages, close } = props;

  const colTitleClass = "text-right my-a";
  const rowClass = "py-2";
  const colSize = 3;

  let enabled: Language[] = [];
  if (series?.languages instanceof Array) {
    enabled = series?.languages.map((lang) => {
      return {
        code2: lang.code2,
        code3: lang.code3,
        enabled: true,
        name: lang.name,
      };
    });
  }

  return (
    <Modal size="lg" show={series !== undefined} onHide={close}>
      <Modal.Header closeButton>{series?.title}</Modal.Header>
      <Modal.Body>
        <Container fluid>
          <Row className={rowClass}>
            <Col sm={colSize} className={colTitleClass}>
              Audio Profile
            </Col>
            <Col>{series?.audio_language.name}</Col>
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
                defaultChecked={series?.hearing_impaired === "True"}
              ></Form.Check>
            </Col>
          </Row>
          <Row className={rowClass}>
            <Col sm={colSize} className={colTitleClass}>
              Forced
            </Col>
            {/* TODO: Make it useable */}
            <Col>{series?.forced}</Col>
          </Row>
        </Container>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="outline-secondary" onClick={close}>
          Cancel
        </Button>
        <Button>Save</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default connect(mapStateToProps)(SeriesEditModal);
