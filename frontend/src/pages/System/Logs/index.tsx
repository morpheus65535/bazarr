import { FunctionComponent, useCallback } from "react";
import { Badge, Container, Group, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useModals } from "@mantine/modals";
import {
  faDownload,
  faFilter,
  faSync,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { useDeleteLogs, useSystemLogs, useSystemSettings } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { Check, LayoutModal, Message, Text } from "@/pages/Settings/components";
import { Environment } from "@/utilities";
import Table from "./table";

const SystemLogsView: FunctionComponent = () => {
  const logs = useSystemLogs();
  const { isFetching, data, refetch } = logs;

  const { mutate, isPending } = useDeleteLogs();

  const download = useCallback(() => {
    window.open(`${Environment.baseUrl}/bazarr.log`);
  }, []);

  useDocumentTitle("Logs - Bazarr (System)");

  const { data: settings } = useSystemSettings();
  const modals = useModals();

  const suffix = () => {
    const include = settings?.log.include_filter;
    const exclude = settings?.log.exclude_filter;
    const includeIndex = include !== "" && include !== undefined ? 1 : 0;
    const excludeIndex = exclude !== "" && exclude !== undefined ? 1 : 0;
    const filters = [
      ["", "I"],
      ["E", "I/E"],
    ];
    const filterStr = filters[excludeIndex][includeIndex];
    const debugStr = settings?.general.debug ? "Debug" : "";
    const spaceStr = debugStr !== "" && filterStr !== "" ? " " : "";
    const suffixStr = debugStr + spaceStr + filterStr;
    return suffixStr;
  };

  const openFilterModal = () => {
    const callbackModal = (close: boolean) => {
      if (close) {
        modals.closeModal(id);
      }
    };

    const id = modals.openModal({
      title: "Set Log Debug and Filter Options",
      children: (
        <LayoutModal callbackModal={callbackModal}>
          <Stack>
            <Check label="Debug" settingKey="settings-general-debug"></Check>
            <Message>Debug logging should only be enabled temporarily</Message>
            <Text
              label="Include Filter"
              settingKey="settings-log-include_filter"
            ></Text>
            <Text
              label="Exclude Filter"
              settingKey="settings-log-exclude_filter"
            ></Text>
            <Check
              label="Use Regular Expressions (Regex)"
              settingKey="settings-log-use_regex"
            ></Check>
            <Check
              label="Ignore Case"
              settingKey="settings-log-ignore_case"
            ></Check>
          </Stack>
        </LayoutModal>
      ),
    });
  };

  return (
    <Container fluid px={0}>
      <QueryOverlay result={logs}>
        <Toolbox>
          <Group gap="xs">
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
              loading={isPending}
              icon={faTrash}
              onClick={() => mutate()}
            >
              Empty
            </Toolbox.Button>
            <Toolbox.Button
              loading={isPending}
              icon={faFilter}
              onClick={openFilterModal}
              rightSection={
                suffix() !== "" ? (
                  <Badge size="xs" radius="sm">
                    {suffix()}
                  </Badge>
                ) : (
                  <></>
                )
              }
            >
              Filter
            </Toolbox.Button>
          </Group>
        </Toolbox>
        <Table logs={data ?? []}></Table>
      </QueryOverlay>
    </Container>
  );
};

export default SystemLogsView;
