import React, { FunctionComponent, useMemo } from "react";
import { Badge, Card, Container, Row } from "react-bootstrap";
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
              <InfoElement key={idx} {...v}></InfoElement>
            ))}
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

const footerBadgeCls = "mr-2";

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
      <Card.Body>
        <Card.Title>
          <span>{name}</span>
        </Card.Title>
        <Card.Subtitle>From newest to oldest</Card.Subtitle>
        <Card.Text className="mt-3">
          {infos.map((v, idx) => (
            <li key={idx}>{v}</li>
          ))}
        </Card.Text>
      </Card.Body>
      <Card.Footer>
        <Badge className={footerBadgeCls} variant="info">
          {date}
        </Badge>
        <Badge
          className={footerBadgeCls}
          variant={prerelease ? "danger" : "success"}
        >
          {prerelease ? "Development" : "Master"}
        </Badge>
        <Badge className={footerBadgeCls} hidden={!current} variant="primary">
          Installed
        </Badge>
      </Card.Footer>
    </Card>
  );
};

export default ReleasesView;
