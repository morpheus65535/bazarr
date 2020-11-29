import React, { FunctionComponent } from "react";
import { Image, Container, Row, Col, Badge } from "react-bootstrap";

interface Props {
  item: BasicItem;
  details?: any[];
}

const ItemOverview: FunctionComponent<Props> = (props) => {
  const badgeClass = "mr-2";
  const infoRowClass = "mb-2";

  const { item, details } = props;

  let subtitleLanguages: JSX.Element[] = [];

  if (item.languages instanceof Array) {
    subtitleLanguages = item.languages.map((val) => {
      return (
        <Badge variant="secondary" className={badgeClass} key={val.name}>
          {val.name}
        </Badge>
      );
    });
  }

  const detailBadges = details?.map((val, idx) => (
    <Badge variant="secondary" className={badgeClass} key={idx}>
      {val}
    </Badge>
  ));

  return (
    <Container fluid className="p-4">
      <Row>
        <Col sm="auto">
          <Image src={item.poster}></Image>
        </Col>
        <Col>
          <Container fluid>
            <Row className={infoRowClass}>
              <h1>{item.title}</h1>
              {/* Tooltip */}
            </Row>
            <Row className={infoRowClass}>{detailBadges}</Row>
            <Row className={infoRowClass}>{subtitleLanguages}</Row>
            <Row className={infoRowClass}>
              <Badge variant="secondary" className={badgeClass}>
                Hearing-Impaired: {item.hearing_impaired}
              </Badge>
              <Badge variant="secondary" className={badgeClass}>
                Forced: {item.forced}
              </Badge>
            </Row>
            <Row className={infoRowClass}>
              <span>{item.overview}</span>
            </Row>
          </Container>
        </Col>
      </Row>
    </Container>
  );
};

export default ItemOverview;
