import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faDiscord,
  faGithub,
  faWikipediaW,
} from "@fortawesome/free-brands-svg-icons";
import { faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Col, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemHealth, useSystemStatus } from "../../@redux/hooks";
import { AsyncOverlay } from "../../components";
import { GithubRepoRoot } from "../../constants";
import Table from "./table";

interface InfoProps {
  title: string;
  children: React.ReactNode;
}

function CRow(props: InfoProps): JSX.Element {
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
  link: string;
  children: string;
}

function Label(props: IconProps): JSX.Element {
  const { icon, link, children } = props;
  return (
    <React.Fragment>
      <FontAwesomeIcon icon={icon} style={{ width: "2rem" }}></FontAwesomeIcon>
      <a href={link} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    </React.Fragment>
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

interface Props {}

const SystemStatusView: FunctionComponent<Props> = () => {
  const health = useSystemHealth();
  const status = useSystemStatus();

  return (
    <Container className="p-5">
      <Helmet>
        <title>Status - Bazarr (System)</title>
      </Helmet>
      <Row>
        <InfoContainer title="Health">
          <AsyncOverlay ctx={health}>
            {({ content }) => {
              return <Table health={content ?? []}></Table>;
            }}
          </AsyncOverlay>
        </InfoContainer>
      </Row>
      <Row>
        <InfoContainer title="About">
          <CRow title="Bazarr Version">
            <span>{status?.bazarr_version}</span>
          </CRow>
          <CRow title="Sonarr Version">
            <span>{status?.sonarr_version}</span>
          </CRow>
          <CRow title="Radarr Version">
            <span>{status?.radarr_version}</span>
          </CRow>
          <CRow title="Operating System">
            <span>{status?.operating_system}</span>
          </CRow>
          <CRow title="Python Version">
            <span>{status?.python_version}</span>
          </CRow>
          <CRow title="Bazarr Directory">
            <span>{status?.bazarr_directory}</span>
          </CRow>
          <CRow title="Bazarr Config Directory">
            <span>{status?.bazarr_config_directory}</span>
          </CRow>
        </InfoContainer>
      </Row>
      <Row>
        <InfoContainer title="More Info">
          <CRow title="Home Page">
            <Label icon={faPaperPlane} link="https://www.bazarr.media/">
              Bazarr Website
            </Label>
          </CRow>
          <CRow title="Source">
            <Label icon={faGithub} link={GithubRepoRoot}>
              Bazarr on Github
            </Label>
          </CRow>
          <CRow title="Wiki">
            <Label icon={faWikipediaW} link="https://wiki.bazarr.media">
              Bazarr Wiki
            </Label>
          </CRow>
          <CRow title="Discord">
            <Label icon={faDiscord} link="https://discord.gg/MH2e2eb">
              Bazarr on Discord
            </Label>
          </CRow>
        </InfoContainer>
      </Row>
    </Container>
  );
};

export default SystemStatusView;
