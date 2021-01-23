import React, { FunctionComponent } from "react";
import { Image, Container, Row, Col, Badge } from "react-bootstrap";

interface Props {
  item: ExtendItem;
  details?: any[];
}

const ItemOverview: FunctionComponent<Props> = (props) => {
  const badgeClass = "mr-2 my-1 text-overflow-ellipsis";
  const infoRowClass = "text-white";

  const { item, details } = props;

  let subtitleLanguages: JSX.Element[] = [];

  if (item.languages instanceof Array) {
    subtitleLanguages = item.languages.map((val) => {
      return (
        <Badge
          title={val.name}
          variant="secondary"
          className={badgeClass}
          key={val.name}
        >
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
    <Container
      fluid
      style={{
        backgroundImage: `url('${item.fanart}')`,
      }}
    >
      <Row
        className="p-4 pb-5"
        style={{
          backgroundColor: "rgba(0,0,0,0.7)",
        }}
      >
        <Col sm="auto">
          <Image
            style={{
              maxHeight: 250,
            }}
            src={item.poster}
          ></Image>
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
              {/* <Badge
                variant="secondary"
                className={badgeClass}
                hidden={!item.hearing_impaired}
              >
                Hearing-Impaired
              </Badge>
              <Badge
                variant="secondary"
                className={badgeClass}
                hidden={item.forced === "False"}
              >
                Forced
              </Badge> */}
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
