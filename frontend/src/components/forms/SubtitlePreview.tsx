import { FunctionComponent, memo, useMemo, useState } from "react";
import {
  Alert,
  Badge,
  Center,
  CloseButton,
  em,
  Group,
  Highlight,
  LoadingOverlay,
  ScrollArea,
  Stack,
  Text,
  TextInput,
  Tooltip,
} from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
import {
  faCircleExclamation,
  faMagnifyingGlass,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSubtitleContents } from "@/apis/hooks";
import { withModal } from "@/modules/modals";
import styles from "./SubtitlePreview.module.scss";

const MOBILE_QUERY = `(max-width: ${em(750)})`;

const formatTimestamp = (t: SubtitleContents.LineTime) => {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${pad(t.hours)}:${pad(t.minutes)}:${pad(t.seconds)}`;
};

const getBasename = (path: string) => path.split(/[\\/]/).pop() || path;

const isTrue = (value?: PythonBoolean) => value === "True";

interface LineRowProps {
  line: SubtitleContents.Line;
  highlight: string;
}

const SubtitleLineRow = memo(function SubtitleLineRow({
  line,
  highlight,
}: LineRowProps) {
  return (
    <Group className={styles.line} gap="md" align="flex-start" wrap="nowrap">
      <Text ff="monospace" size="xs" c="dimmed" className={styles.timestamp}>
        {formatTimestamp(line.start)}
      </Text>
      <Highlight
        dir="auto"
        highlight={highlight}
        style={{ whiteSpace: "pre-wrap" }}
      >
        {line.content}
      </Highlight>
    </Group>
  );
});

interface PreviewHeaderProps {
  path: string;
  selection: FormType.ModifySubtitle;
  countLabel: string | null;
}

const PreviewHeader: FunctionComponent<PreviewHeaderProps> = ({
  path,
  selection,
  countLabel,
}) => (
  <Group gap="xs" wrap="wrap" align="center">
    <Tooltip label={path} multiline maw={480} withArrow>
      <Text fw={600} style={{ wordBreak: "break-all" }}>
        {getBasename(path)}
      </Text>
    </Tooltip>
    {selection.language && (
      <Badge variant="light">{selection.language.toUpperCase()}</Badge>
    )}
    {isTrue(selection.hi) && (
      <Badge variant="light" color="cyan">
        HI
      </Badge>
    )}
    {isTrue(selection.forced) && (
      <Badge variant="light" color="grape">
        Forced
      </Badge>
    )}
    {countLabel && (
      <Badge variant="outline" color="gray" ml="auto">
        {countLabel}
      </Badge>
    )}
  </Group>
);

interface Props {
  selections: FormType.ModifySubtitle[];
}

const SubtitlePreviewView: FunctionComponent<Props> = ({ selections }) => {
  const selection = selections[0];
  const path = selection?.path ?? null;

  const isMobile = useMediaQuery(MOBILE_QUERY);

  const [search, setSearch] = useState("");
  // Search is hidden on mobile, so ignore any term carried over from a
  // desktop-width search when the viewport shrinks.
  const term = isMobile ? "" : search.trim();

  const query = useSubtitleContents(path ?? "");
  const lines = useMemo(() => query.data ?? [], [query.data]);

  const filtered = useMemo(() => {
    const needle = term.toLowerCase();
    if (!needle) return lines;
    return lines.filter((line) => line.content.toLowerCase().includes(needle));
  }, [lines, term]);

  const isEmpty = !query.isLoading && !query.isError && lines.length === 0;

  const countLabel =
    query.isLoading || query.isError
      ? null
      : term
        ? `${filtered.length} / ${lines.length} lines`
        : `${lines.length} lines`;

  const header =
    path !== null ? (
      <PreviewHeader
        path={path}
        selection={selection}
        countLabel={countLabel}
      />
    ) : null;

  return (
    <Stack pos="relative" gap="sm">
      <LoadingOverlay
        visible={query.isLoading}
        zIndex={1000}
        overlayProps={{ radius: "sm", blur: 2 }}
      />

      {/* On desktop the header stays pinned above the scrolling list. On mobile
          it is rendered inside the scroll area (below) so it scrolls away. */}
      {!isMobile && header}

      {query.isError ? (
        <Alert
          color="red"
          variant="light"
          icon={<FontAwesomeIcon icon={faCircleExclamation} />}
          title="Unable to read subtitle"
        >
          This subtitle could not be read. Only UTF-8 encoded SRT files can be
          previewed.
        </Alert>
      ) : isEmpty ? (
        <Alert color="yellow" variant="light">
          No content could be read from this subtitle file.
        </Alert>
      ) : (
        <>
          {!isMobile && (
            <TextInput
              data-autofocus
              placeholder="Search text..."
              value={search}
              onChange={(e) => setSearch(e.currentTarget.value)}
              leftSection={<FontAwesomeIcon icon={faMagnifyingGlass} />}
              rightSection={
                search ? (
                  <CloseButton
                    size="sm"
                    aria-label="Clear search"
                    onClick={() => setSearch("")}
                  />
                ) : null
              }
            />
          )}
          <ScrollArea.Autosize
            mah={isMobile ? "calc(100dvh - 120px)" : "60vh"}
            offsetScrollbars
          >
            {isMobile && header && <Stack mb="sm">{header}</Stack>}
            {filtered.length === 0 ? (
              <Center py="xl">
                <Text c="dimmed" size="sm">
                  No lines match &quot;{term}&quot;.
                </Text>
              </Center>
            ) : (
              <Stack gap={2}>
                {filtered.map((line) => (
                  <SubtitleLineRow
                    key={line.index}
                    line={line}
                    highlight={term}
                  />
                ))}
              </Stack>
            )}
          </ScrollArea.Autosize>
        </>
      )}
    </Stack>
  );
};

export const SubtitlePreviewModal = withModal(
  SubtitlePreviewView,
  "subtitle-preview",
  {
    title: "Preview Subtitle",
    size: "xl",
  },
);

export default SubtitlePreviewView;
