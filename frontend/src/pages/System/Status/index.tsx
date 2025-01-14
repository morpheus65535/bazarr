import {
  FunctionComponent,
  JSX,
  PropsWithChildren,
  ReactNode,
  useCallback,
  useState,
} from "react";
import {
  Anchor,
  Container,
  Divider,
  Grid,
  Space,
  Stack,
  Text,
} from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faDiscord,
  faGithub,
  faWikipediaW,
} from "@fortawesome/free-brands-svg-icons";
import { faCode, faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSystemHealth, useSystemStatus } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import { GithubRepoRoot } from "@/constants";
import { Environment, useInterval } from "@/utilities";
import {
  divisorDay,
  divisorHour,
  divisorMinute,
  divisorSecond,
  formatTime,
} from "@/utilities/time";
import Table from "./table";

interface InfoProps {
  title: string;
  children: ReactNode;
}

function Row(props: InfoProps): JSX.Element {
  const { title, children } = props;
  return (
    <Grid columns={10}>
      <Grid.Col span={2}>
        <Text size="sm" ta="right" fw="bold">
          {title}
        </Text>
      </Grid.Col>
      <Grid.Col span={3}>
        <Text size="sm"> {children}</Text>
      </Grid.Col>
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
      <Anchor href={link} target="_blank" rel="noopener noreferrer">
        {children}
      </Anchor>
    </>
  );
}

interface InfoContainerProps {
  title: string;
}

const InfoContainer: FunctionComponent<
  PropsWithChildren<InfoContainerProps>
> = ({ title, children }) => {
  return (
    <Stack>
      <Divider
        labelPosition="left"
        label={
          <Text size="md" fw="bold">
            {title}
          </Text>
        }
      ></Divider>
      {children}
      <Space />
    </Stack>
  );
};

const SystemStatusView: FunctionComponent = () => {
  const health = useSystemHealth();
  const { data: status } = useSystemStatus();

  const [uptime, setUptime] = useState<string>();

  const update = useCallback(() => {
    const startTime = status?.start_time;
    if (startTime) {
      // Current time in seconds
      const currentTime = Math.floor(Date.now() / 1000);

      const uptimeInSeconds = currentTime - startTime;

      const uptime: string = formatTime(uptimeInSeconds, [
        { unit: "d", divisor: divisorDay },
        { unit: "h", divisor: divisorHour },
        { unit: "m", divisor: divisorMinute },
        { unit: "s", divisor: divisorSecond },
      ]);

      setUptime(uptime);
    }
  }, [status?.start_time]);

  useInterval(update, 1000);

  useDocumentTitle("Status - Bazarr (System)");

  return (
    <Container fluid>
      <Stack>
        <InfoContainer title="Health">
          <QueryOverlay result={health}>
            <Table health={health.data ?? []}></Table>
          </QueryOverlay>
        </InfoContainer>
        <InfoContainer title="About">
          <Row title="Bazarr Version">{status?.bazarr_version}</Row>
          {status?.package_version !== "" && (
            <Row title="Package Version">{status?.package_version}</Row>
          )}
          <Row title="Sonarr Version">{status?.sonarr_version}</Row>
          <Row title="Radarr Version">{status?.radarr_version}</Row>
          <Row title="Operating System">{status?.operating_system}</Row>
          <Row title="Python Version">{status?.python_version}</Row>
          <Row title="Database Engine">{status?.database_engine}</Row>
          <Row title="Database Version">{status?.database_migration}</Row>
          <Row title="Bazarr Directory">{status?.bazarr_directory}</Row>
          <Row title="Bazarr Config Directory">
            {status?.bazarr_config_directory}
          </Row>
          <Row title="Uptime">{uptime}</Row>
          <Row title="Time Zone">{status?.timezone}</Row>
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
          <Row title="API documentation">
            <Label icon={faCode} link={`${Environment.baseUrl}/api/`}>
              Swagger UI
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
