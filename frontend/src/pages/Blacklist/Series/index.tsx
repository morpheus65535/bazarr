import { useEpisodeBlacklist, useEpisodeDeleteBlacklist } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { Container, Stack } from "@mantine/core";
import { FunctionComponent } from "react";
import { Helmet } from "react-helmet";
import Table from "./table";

const BlacklistSeriesView: FunctionComponent = () => {
  const blacklist = useEpisodeBlacklist();
  const { mutateAsync } = useEpisodeDeleteBlacklist();

  const { data } = blacklist;
  return (
    <QueryOverlay result={blacklist}>
      <Container fluid px={0}>
        <Helmet>
          <title>Series Blacklist - Bazarr</title>
        </Helmet>
        <Stack>
          <Toolbox>
            <Toolbox.MutateButton
              icon={faTrash}
              disabled={data?.length === 0}
              promise={() => mutateAsync({ all: true })}
            >
              Remove All
            </Toolbox.MutateButton>
          </Toolbox>
          <Table blacklist={data ?? []}></Table>
        </Stack>
      </Container>
    </QueryOverlay>
  );
};

export default BlacklistSeriesView;
