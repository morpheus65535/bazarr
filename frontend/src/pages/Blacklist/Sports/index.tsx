import { FunctionComponent } from "react";
import { Container, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useSportsBlacklist, useSportsDeleteBlacklist } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import Table from "./table";

const BlacklistSportsView: FunctionComponent = () => {
  const blacklist = useSportsBlacklist();
  const { mutateAsync } = useSportsDeleteBlacklist();

  useDocumentTitle(`Sports Blacklist - ${useInstanceName()}`);

  const { data } = blacklist;
  return (
    <QueryOverlay result={blacklist}>
      <Container fluid px={0}>
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

export default BlacklistSportsView;
