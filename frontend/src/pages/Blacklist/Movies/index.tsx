import { FunctionComponent } from "react";
import { Container, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import {
  useMovieBlacklist,
  useMovieDeleteBlacklist,
} from "@/apis/hooks/movies";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import Table from "./table";

const BlacklistMoviesView: FunctionComponent = () => {
  const blacklist = useMovieBlacklist();
  const { data } = blacklist;

  const { mutateAsync } = useMovieDeleteBlacklist();

  useDocumentTitle("Movies Blacklist - Bazarr");

  return (
    <Container fluid px={0}>
      <QueryOverlay result={blacklist}>
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
      </QueryOverlay>
    </Container>
  );
};

export default BlacklistMoviesView;
