import { FunctionComponent } from "react";
import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useSystemAnnouncements } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import Table from "./table";

const SystemAnnouncementsView: FunctionComponent = () => {
  const announcements = useSystemAnnouncements();

  const { data } = announcements;

  useDocumentTitle("Announcements - Bazarr (System)");

  return (
    <QueryOverlay result={announcements}>
      <Container fluid px={0}>
        <Table announcements={data ?? []}></Table>
      </Container>
    </QueryOverlay>
  );
};

export default SystemAnnouncementsView;
