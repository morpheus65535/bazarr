import { useDeleteLogs, useSystemLogs } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { Environment } from "@/utilities";
import { faDownload, faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import { Container, Group } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { FunctionComponent, useCallback } from "react";
import Table from "./table";

const SystemLogsView: FunctionComponent = () => {
  const logs = useSystemLogs();
  const { isFetching, data, refetch } = logs;

  const { mutate, isLoading } = useDeleteLogs();

  const download = useCallback(() => {
    window.open(`${Environment.baseUrl}/bazarr.log`);
  }, []);

  useDocumentTitle("Logs - Bazarr (System)");

  return (
    <Container fluid px={0}>
      <QueryOverlay result={logs}>
        <Toolbox>
          <Group spacing="xs">
            <Toolbox.Button
              loading={isFetching}
              icon={faSync}
              onClick={() => refetch()}
            >
              Refresh
            </Toolbox.Button>
            <Toolbox.Button icon={faDownload} onClick={download}>
              Download
            </Toolbox.Button>
            <Toolbox.Button
              loading={isLoading}
              icon={faTrash}
              onClick={() => mutate()}
            >
              Empty
            </Toolbox.Button>
          </Group>
        </Toolbox>
        <Table logs={data ?? []}></Table>
      </QueryOverlay>
    </Container>
  );
};

export default SystemLogsView;
