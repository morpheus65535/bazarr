import { useSystemHealth, useSystemStatus } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import { GithubRepoRoot } from "@/constants";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faDiscord,
  faGithub,
  faWikipediaW,
} from "@fortawesome/free-brands-svg-icons";
import { faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Container, Divider, Grid, Stack, Text } from "@mantine/core";
import moment from "moment";
import { FunctionComponent, ReactNode, useState } from "react";
import { Helmet } from "react-helmet";
import { useIntervalWhen } from "rooks";
import Table from "./table";

interface InfoProps {
  title: string;
  children: ReactNode;
}

function Row(props: InfoProps): JSX.Element {
  const { title, children } = props;
  return (
    <Grid>
      <Grid.Col span={5}>
        <Text weight="bold">{title}</Text>
      </Grid.Col>
      <Grid.Col span={12 - 5}>{children}</Grid.Col>
    </Grid>
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
    <>
      <FontAwesomeIcon icon={icon} style={{ width: "2rem" }}></FontAwesomeIcon>
      <a href={link} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    </>
  );
}

const InfoContainer: FunctionComponent<{ title: string }> = ({
  title,
  children,
}) => {
  return (
    <Stack>
      <h4>{title}</h4>
      <Divider></Divider>
      {children}
    </Stack>
  );
};

const SystemStatusView: FunctionComponent = () => {
  const health = useSystemHealth();
  const { data: status } = useSystemStatus();

  const [uptime, setState] = useState<string>();
  const [intervalWhenState] = useState(true);

  useIntervalWhen(
    () => {
      if (status) {
        const duration = moment.duration(
            moment().utc().unix() - status.start_time,
            "seconds"
          ),
          days = duration.days(),
          hours = duration.hours().toString().padStart(2, "0"),
          minutes = duration.minutes().toString().padStart(2, "0"),
          seconds = duration.seconds().toString().padStart(2, "0");
        setState(days + "d " + hours + ":" + minutes + ":" + seconds);
      }
    },
    1000,
    intervalWhenState,
    true
  );

  return (
    <Container fluid>
      <Helmet>
        <title>Status - Bazarr (System)</title>
      </Helmet>
      <Stack>
        <InfoContainer title="Health">
          <QueryOverlay result={health}>
            <Table health={health.data ?? []}></Table>
          </QueryOverlay>
        </InfoContainer>
        <InfoContainer title="About">
          <Row title="Bazarr Version">
            <span>{status?.bazarr_version}</span>
          </Row>
          {status?.package_version !== "" && (
            <Row title="Package Version">
              <span>{status?.package_version}</span>
            </Row>
          )}
          <Row title="Sonarr Version">
            <span>{status?.sonarr_version}</span>
          </Row>
          <Row title="Radarr Version">
            <span>{status?.radarr_version}</span>
          </Row>
          <Row title="Operating System">
            <span>{status?.operating_system}</span>
          </Row>
          <Row title="Python Version">
            <span>{status?.python_version}</span>
          </Row>
          <Row title="Bazarr Directory">
            <span>{status?.bazarr_directory}</span>
          </Row>
          <Row title="Bazarr Config Directory">
            <span>{status?.bazarr_config_directory}</span>
          </Row>
          <Row title="Uptime">
            <span>{uptime}</span>
          </Row>
        </InfoContainer>
        <InfoContainer title="More Info">
          <Row title="Home Page">
            <Label icon={faPaperPlane} link="https://www.bazarr.media/">
              Bazarr Website
            </Label>
          </Row>
          <Row title="Source">
            <Label icon={faGithub} link={GithubRepoRoot}>
              Bazarr on Github
            </Label>
          </Row>
          <Row title="Wiki">
            <Label icon={faWikipediaW} link="https://wiki.bazarr.media">
              Bazarr Wiki
            </Label>
          </Row>
          <Row title="Discord">
            <Label icon={faDiscord} link="https://discord.gg/MH2e2eb">
              Bazarr on Discord
            </Label>
          </Row>
        </InfoContainer>
      </Stack>
    </Container>
  );
};

export default SystemStatusView;
