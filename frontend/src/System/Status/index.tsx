import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { connect } from "react-redux";
import { UpdateSystemStatus } from "../../redux/actions/system";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import {
  faGithub,
  faWikipediaW,
  faDiscord,
} from "@fortawesome/free-brands-svg-icons";

interface Props {
  status: SystemStatusResult;
  update: () => void;
}

function mapStateToProps({ system }: StoreState) {
  const { status } = system;
  return {
    status: status.items,
  };
}

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

class SystemStatus extends React.Component<Props, {}> {
  componentDidMount() {
    this.props.update();
  }
  render(): JSX.Element {
    const {
      bazarr_version,
      sonarr_version,
      radarr_version,
      operating_system,
      python_version,
      bazarr_config_directory,
      bazarr_directory,
    } = this.props.status;

    const about: JSX.Element = (
      <div>
        <h2>About</h2>
        <hr></hr>
        <InfoRow title="Bazarr Version">
          <span>{bazarr_version}</span>
        </InfoRow>
        <InfoRow title="Sonarr Version">
          <span>{sonarr_version}</span>
        </InfoRow>
        <InfoRow title="Radarr Version">
          <span>{radarr_version}</span>
        </InfoRow>
        <InfoRow title="Operating System">
          <span>{operating_system}</span>
        </InfoRow>
        <InfoRow title="Python Version">
          <span>{python_version}</span>
        </InfoRow>
        <InfoRow title="Bazarr Directory">
          <span>{bazarr_directory}</span>
        </InfoRow>
        <InfoRow title="Bazarr Config Directory">
          <span>{bazarr_config_directory}</span>
        </InfoRow>
      </div>
    );

    const more: JSX.Element = (
      <div className="my-4">
        <h2>More Info</h2>
        <hr></hr>
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
      </div>
    );

    return (
      <Container fluid className="p-5">
        {about}
        {more}
      </Container>
    );
  }
}

export default connect(mapStateToProps, {
  update: UpdateSystemStatus,
})(SystemStatus);
