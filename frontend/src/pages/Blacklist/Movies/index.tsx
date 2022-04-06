import {
  useMovieBlacklist,
  useMovieDeleteBlacklist,
} from "@/apis/hooks/movies";
import { ContentHeader } from "@/components";
import { QueryOverlay } from "@/components/async";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { Container, Stack } from "@mantine/core";
import { FunctionComponent } from "react";
import { Helmet } from "react-helmet";
import Table from "./table";

const BlacklistMoviesView: FunctionComponent = () => {
  const blacklist = useMovieBlacklist();
  const { data } = blacklist;

  const { mutateAsync } = useMovieDeleteBlacklist();

  return (
    <Container fluid px={0}>
      <QueryOverlay result={blacklist}>
        <Helmet>
          <title>Movies Blacklist - Bazarr</title>
        </Helmet>
        <Stack>
          <ContentHeader>
            <ContentHeader.AsyncButton
              icon={faTrash}
              disabled={data?.length === 0}
              promise={() => mutateAsync({ all: true })}
            >
              Remove All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Table blacklist={data ?? []}></Table>
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

export default BlacklistMoviesView;
