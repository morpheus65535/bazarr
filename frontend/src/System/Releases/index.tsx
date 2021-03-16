import React, { FunctionComponent, useMemo } from "react";
import { Badge, Card, Col, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { systemUpdateReleases } from "../../@redux/actions";
import { useReduxAction, useReduxStore } from "../../@redux/hooks/base";
import { AsyncStateOverlay } from "../../components";
import { useAutoUpdate } from "../../utilites/hooks";

interface Props {}

const ReleasesView: FunctionComponent<Props> = () => {
  const releases = useReduxStore(({ system }) => system.releases);
  const update = useReduxAction(systemUpdateReleases);
  useAutoUpdate(update);

  return (
    <AsyncStateOverlay state={releases}>
      {(item) => (
        <Container fluid className="px-5 py-4 bg-light">
          <Helmet>
            <title>Releases - Bazarr (System)</title>
          </Helmet>
          <Row>
            {item.map((v, idx) => (
              <Col xs={12}>
                <InfoElement key={idx} {...v}></InfoElement>
              </Col>
            ))}
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
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

export default ReleasesView;
