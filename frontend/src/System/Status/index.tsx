import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { connect } from "react-redux";
import { UpdateSystemStatus } from "../../redux/actions/system";
import { StoreState } from "../../redux/types";

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

    return (
      <Container fluid className="p-5">
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
      </Container>
    );
  }
}

export default connect(mapStateToProps, {
  update: UpdateSystemStatus,
})(SystemStatus);
