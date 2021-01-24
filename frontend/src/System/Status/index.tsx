import React, { FunctionComponent, useEffect, useMemo } from "react";
import { Container, Row, Col } from "react-bootstrap";
import { connect } from "react-redux";
import { UpdateSystemStatus } from "../../@redux/actions";
import { Helmet } from "react-helmet";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import {
  faGithub,
  faWikipediaW,
  faDiscord,
} from "@fortawesome/free-brands-svg-icons";

interface InfoProps {
  title: string;
  children: React.ReactNode;
}

function InfoRow(props: InfoProps): JSX.Element {
  const { title, children } = props;
  return (
    <Row>
      <Col sm={4}>
        <b>{title}</b>
      </Col>
      <Col>{children}</Col>
    </Row>
  );
}

interface IconProps {
  icon: IconDefinition;
  children: React.ReactNode;
}

function IconLabel(props: IconProps): JSX.Element {
  const { icon, children } = props;
  return (
    <Row>
      <Col sm={1}>
        <FontAwesomeIcon icon={icon} className="mr-2"></FontAwesomeIcon>
      </Col>
      <Col>{children}</Col>
    </Row>
  );
}

const InfoContainer: FunctionComponent<{ title: string }> = ({
  title,
  children,
}) => {
  return (
    <Container className="py-3">
      <h4>{title}</h4>
      <hr></hr>
      {children}
    </Container>
  );
};

interface Props {
  status?: SystemStatusResult;
  update: () => void;
}

function mapStateToProps({ system }: StoreState) {
  const { status } = system;
  return {
    status: status.items,
  };
}

const SystemStatusView: FunctionComponent<Props> = ({ status, update }) => {
  useEffect(() => update(), [update]);

  const about = useMemo(
    () => (
      <InfoContainer title="About">
        <InfoRow title="Bazarr Version">
          <span>{status?.bazarr_version}</span>
        </InfoRow>
        <InfoRow title="Sonarr Version">
          <span>{status?.sonarr_version}</span>
        </InfoRow>
        <InfoRow title="Radarr Version">
          <span>{status?.radarr_version}</span>
        </InfoRow>
        <InfoRow title="Operating System">
          <span>{status?.operating_system}</span>
        </InfoRow>
        <InfoRow title="Python Version">
          <span>{status?.python_version}</span>
        </InfoRow>
        <InfoRow title="Bazarr Directory">
          <span>{status?.bazarr_directory}</span>
        </InfoRow>
        <InfoRow title="Bazarr Config Directory">
          <span>{status?.bazarr_config_directory}</span>
        </InfoRow>
      </InfoContainer>
    ),
    [status]
  );

  const more = useMemo(
    () => (
      <InfoContainer title="More Info">
        <InfoRow title="Home Page">
          <IconLabel icon={faPaperPlane}>
            <a
              href="https://www.bazarr.media/"
              target="_blank"
              rel="noopener noreferrer"
            >
              Bazarr Website
            </a>
          </IconLabel>
        </InfoRow>
        <InfoRow title="Source">
          <IconLabel icon={faGithub}>
            <a
              href="https://github.com/morpheus65535/bazarr"
              target="_blank"
              rel="noopener noreferrer"
            >
              Bazarr on Github
            </a>
          </IconLabel>
        </InfoRow>
        <InfoRow title="Wiki">
          <IconLabel icon={faWikipediaW}>
            <a
              href="https://github.com/morpheus65535/bazarr/wiki"
              target="_blank"
              rel="noopener noreferrer"
            >
              Bazarr Wiki
            </a>
          </IconLabel>
        </InfoRow>
        <InfoRow title="Discord">
          <IconLabel icon={faDiscord}>
            <a
              href="https://discord.gg/MH2e2eb"
              target="_blank"
              rel="noopener noreferrer"
            >
              Bazarr on Discord
            </a>
          </IconLabel>
        </InfoRow>
      </InfoContainer>
    ),
    []
  );

  return (
    <Container fluid className="p-5">
      <Helmet>
        <title>Status - Bazarr (System)</title>
      </Helmet>
      <Row>{about}</Row>
      <Row>{more}</Row>
    </Container>
  );
};

export default connect(mapStateToProps, {
  update: UpdateSystemStatus,
})(SystemStatusView);
