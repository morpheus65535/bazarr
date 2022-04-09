import { useResetProvider, useSystemProviders } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { FunctionComponent } from "react";
import Table from "./table";

const SystemProvidersView: FunctionComponent = () => {
  const providers = useSystemProviders();

  const { isFetching, data, refetch } = providers;

  const { mutate: reset, isLoading: isResetting } = useResetProvider();

  useDocumentTitle("Providers - Bazarr (System)");

  return (
    <QueryOverlay result={providers}>
      <Container fluid px={0}>
        <Toolbox>
          <Toolbox.Button
            loading={isFetching}
            icon={faSync}
            onClick={() => refetch()}
          >
            Refresh
          </Toolbox.Button>
          <Toolbox.Button
            icon={faTrash}
            loading={isResetting}
            onClick={() => reset()}
          >
            Reset
          </Toolbox.Button>
        </Toolbox>
        <Table providers={data ?? []}></Table>
      </Container>
    </QueryOverlay>
  );
};

export default SystemProvidersView;
