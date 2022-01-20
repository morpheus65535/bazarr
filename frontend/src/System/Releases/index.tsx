import React, { FunctionComponent, useMemo } from "react";
import { Badge, Card, Col, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemReleases } from "../../apis";
import { QueryOverlay } from "../../components";
import { BuildKey } from "../../utilities";

interface Props {}

const SystemReleasesView: FunctionComponent<Props> = () => {
  const releases = useSystemReleases();

  return (
    <Container fluid className="px-3 py-4 bg-light">
      <Helmet>
        <title>Releases - Bazarr (System)</title>
      </Helmet>
      <Row>
        <QueryOverlay {...releases}>
          {({ data }) => {
            return (
              <React.Fragment>
                {data?.map((v, idx) => (
                  <Col xs={12} key={BuildKey(idx, v.date)}>
                    <InfoElement {...v}></InfoElement>
                  </Col>
                ))}
              </React.Fragment>
            );
          }}
        </QueryOverlay>
      </Row>
    </Container>
  );
};

const headerBadgeCls = "mr-2";

const InfoElement: FunctionComponent<ReleaseInfo> = ({
  name,
  body,
  date,
  prerelease,
  current,
}) => {
  const infos = useMemo(
    () => body.map((v) => v.replace(/(\s\[.*?\])\(.*?\)/, "")),
    [body]
  );
  return (
    <Card className="mb-4 mx-3 d-flex flex-grow-1">
      <Card.Header>
        <span className={headerBadgeCls}>{name}</span>
        <Badge className={headerBadgeCls} variant="info">
          {date}
        </Badge>
        <Badge
          className={headerBadgeCls}
          variant={prerelease ? "danger" : "success"}
        >
          {prerelease ? "Development" : "Master"}
        </Badge>
        <Badge className={headerBadgeCls} hidden={!current} variant="primary">
          Installed
        </Badge>
      </Card.Header>
      <Card.Body>
        <Card.Text>
          From newest to oldest:
          {infos.map((v, idx) => (
            <li key={idx}>{v}</li>
          ))}
        </Card.Text>
      </Card.Body>
    </Card>
  );
};

export default SystemReleasesView;
