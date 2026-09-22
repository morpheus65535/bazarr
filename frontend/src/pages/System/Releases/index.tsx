import { FunctionComponent, useMemo, ReactNode } from "react";
import {
  Badge,
  Card,
  Container,
  Divider,
  Group,
  List,
  Stack,
  Text,
} from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useSystemReleases } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { QueryOverlay } from "@/components/async";
import { BuildKey } from "@/utilities";

const parseIssueLinks = (text: string): ReactNode[] => {
  const parts: ReactNode[] = [];
  const issueRegex = /#(\d+)/g;
  let lastIndex = 0;
  let match;

  while ((match = issueRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const issueNumber = match[1];
    parts.push(
      <a
        key={`issue-${issueNumber}`}
        href={`https://github.com/morpheus65535/bazarr/issues/${issueNumber}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        #{issueNumber}
      </a>,
    );
    lastIndex = issueRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
};

const SystemReleasesView: FunctionComponent = () => {
  const releases = useSystemReleases();
  const { data } = releases;

  useDocumentTitle(`Releases - ${useInstanceName()} (System)`);

  return (
    <Container size="md" py={12}>
      <QueryOverlay result={releases}>
        <Stack gap="lg">
          {data?.map((v, idx) => (
            <ReleaseCard key={BuildKey(idx, v.date)} {...v}></ReleaseCard>
          ))}
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

const ReleaseCard: FunctionComponent<ReleaseInfo> = ({
  name,
  body,
  date,
  prerelease,
  current,
}) => {
  const infos = useMemo(
    () => body.map((v) => v.replace(/(\s\[.*?\])\(.*?\)/, "")),
    [body],
  );
  return (
    <Card shadow="md" p="lg">
      <Group>
        <Text fw="bold">{name}</Text>
        <Badge color="info">{date}</Badge>
        <Badge color={prerelease ? "warning" : "success"}>
          {prerelease ? "Development" : "Master"}
        </Badge>
        {current && <Badge color="info">Installed</Badge>}
      </Group>
      <Divider my="sm"></Divider>
      <Text>From newest to oldest:</Text>
      <List>
        {infos.map((v, idx) => (
          <List.Item key={idx}>{parseIssueLinks(v)}</List.Item>
        ))}
      </List>
    </Card>
  );
};

export default SystemReleasesView;
