import { useSystemHealth, useSystemStatus } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import { GithubRepoRoot } from "@/constants";
import { Environment, useInterval } from "@/utilities";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faDiscord,
  faGithub,
  faWikipediaW,
} from "@fortawesome/free-brands-svg-icons";
import { faCode, faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
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
import moment from "moment";
import {
  FunctionComponent,
  PropsWithChildren,
  ReactNode,
  useCallback,
  useState,
} from "react";
import Table from "./table";

interface InfoProps {
  title: string;
  children: ReactNode;
}

function Row(props: InfoProps): JSX.Element {
  const { title, children } = props;
  return (
    <Grid>
      <Grid.Col span={6}>
        <Text size="sm" align="right" weight="bold">
          {title}
        </Text>
      </Grid.Col>
      <Grid.Col span={6}>
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
        labelProps={{ size: "medium", weight: "bold" }}
        labelPosition="center"
        label={title}
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
      const duration = moment.duration(
          moment().utc().unix() - startTime,
          "seconds",
        ),
        days = duration.days(),
        hours = duration.hours().toString().padStart(2, "0"),
        minutes = duration.minutes().toString().padStart(2, "0"),
        seconds = duration.seconds().toString().padStart(2, "0");
      setUptime(days + "d " + hours + ":" + minutes + ":" + seconds);
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
