import React, { FunctionComponent, useEffect } from "react";
import { Card, Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { systemUpdateReleases } from "../../@redux/actions";
import { AsyncStateOverlay } from "../../components";

interface Props {
  releases: AsyncState<ReleaseInfo[]>;
  update: () => void;
}

function mapStateToProps({ system }: StoreState) {
  return {
    releases: system.releases,
  };
}

const ReleasesView: FunctionComponent<Props> = ({ releases, update }) => {
  useEffect(() => {
    update();
  }, [update]);

  return (
    <AsyncStateOverlay state={releases}>
      {(item) => (
        <Container fluid className="px-5 py-4 bg-light">
          <Row>
            {item.map((v, idx) => (
              <InfoElement key={idx} release={v}></InfoElement>
            ))}
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

const InfoElement: FunctionComponent<{ release: ReleaseInfo }> = ({
  release,
}) => {
  return (
    <Card className="mb-4 mx-3 d-flex flex-grow-1">
      <Card.Body>
        <Card.Title>
          <span>{release.name}</span>
        </Card.Title>
        <Card.Subtitle>From newest to oldest</Card.Subtitle>
        <Card.Text className="mt-3">
          {release.body.map((v, idx) => (
            <li key={idx}>{v}</li>
          ))}
        </Card.Text>
      </Card.Body>
      <Card.Footer>{release.date}</Card.Footer>
    </Card>
  );
};

export default connect(mapStateToProps, { update: systemUpdateReleases })(
  ReleasesView
);
