import { FunctionComponent, useMemo, useState } from "react";
import {
  Box,
  Button,
  Container,
  em,
  Group,
  Indicator,
  Menu,
  Popover,
  Stack,
  useMantineTheme,
} from "@mantine/core";
import { useDocumentTitle, useMediaQuery } from "@mantine/hooks";
import {
  faChartArea,
  faChartBar,
  faChartLine,
  faCheck,
  faFilter,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { areaY, barY, defineChart, group, lineY } from "@tanstack/charts";
import { Chart } from "@tanstack/charts/react";
import { scaleBand } from "@tanstack/charts/scales/band";
import { scaleLinear } from "@tanstack/charts/scales/linear";
import { tooltip } from "@tanstack/charts/tooltip";
import {
  useHistoryStats,
  useLanguages,
  useSystemProviders,
} from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { Selector, Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { useSelectorOptions } from "@/utilities";
import { actionOptions, timeFrameOptions } from "./options";
import styles from "./HistoryStats.module.scss";

const MOBILE_QUERY = `(max-width: ${em(750)})`;

type ChartType = "bar" | "line" | "area";

interface HistoryRow {
  date: string;
  type: "Movies" | "Series";
  count: number;
}

const HistoryStats: FunctionComponent = () => {
  const { data: providers } = useSystemProviders(true);

  const providerOptions = useSelectorOptions(providers ?? [], (v) => v.name);

  const { data: historyLanguages } = useLanguages(true);

  const languageOptions = useSelectorOptions(
    historyLanguages ?? [],
    (value) => value.name,
  );

  const [timeFrame, setTimeFrame] = useState<History.TimeFrameOptions>("month");
  const [action, setAction] = useState<Nullable<History.ActionOptions>>(null);
  const [lang, setLanguage] = useState<Nullable<Language.Server>>(null);
  const [provider, setProvider] = useState<Nullable<System.Provider>>(null);
  const [filtersOpened, setFiltersOpened] = useState(false);
  const [chartType, setChartType] = useState<ChartType>("bar");

  const stats = useHistoryStats(timeFrame, action, provider, lang);
  const { data } = stats;

  const theme = useMantineTheme();

  const chartData = useMemo<HistoryRow[]>(() => {
    if (!data) return [];

    // Merge by date, summing duplicates
    const byDate = new Map<string, { movies?: number; series?: number }>();

    for (const v of data.movies) {
      const existing = byDate.get(v.date) ?? {};
      existing.movies = (existing.movies ?? 0) + v.count;
      byDate.set(v.date, existing);
    }

    for (const v of data.series) {
      const existing = byDate.get(v.date) ?? {};
      existing.series = (existing.series ?? 0) + v.count;
      byDate.set(v.date, existing);
    }

    // Convert to long format, sorted by date
    const rows: HistoryRow[] = [];
    const sortedDates = Array.from(byDate.keys()).sort();

    for (const date of sortedDates) {
      const entry = byDate.get(date)!;
      if (entry.movies !== undefined) {
        rows.push({ date, type: "Movies", count: entry.movies });
      }
      if (entry.series !== undefined) {
        rows.push({ date, type: "Series", count: entry.series });
      }
    }

    return rows;
  }, [data]);

  const isMobile = useMediaQuery(MOBILE_QUERY);

  const definition = useMemo(() => {
    const seriesColor = theme.colors.blue[4];
    const moviesColor = theme.colors.yellow[4];
    const getColor = (d: HistoryRow) =>
      d.type === "Series" ? seriesColor : moviesColor;

    const baseOptions = {
      x: "date" as const,
      y: "count" as const,
      color: "type" as const,
      key: (d: HistoryRow) => `${d.date}-${d.type}`,
    };

    const createMark = () => {
      switch (chartType) {
        case "line":
          return lineY(chartData, {
            ...baseOptions,
            stroke: getColor,
            strokeWidth: 2.5,
            points: true,
          });
        case "area":
          return areaY(chartData, {
            ...baseOptions,
            fill: getColor,
            fillOpacity: 0.25,
            stroke: getColor,
            strokeWidth: 1.5,
          });
        default:
          return barY(chartData, {
            ...baseOptions,
            layout: group(),
            fill: getColor,
          });
      }
    };

    return defineChart({
      marks: [createMark()],
      x: {
        scale: () => scaleBand().padding(isMobile ? 0.12 : 0.18),
      },
      y: {
        scale: scaleLinear,
        nice: true,
        grid: true,
        axis: {
          ticks: { format: (value: number) => `${Math.round(value)}` },
        },
      },
      tooltip: {
        use: tooltip,
        items: [
          {
            channel: "x",
            label: "Date",
          },
          {
            channel: "y",
            label: "Count",
            text: (point) => `${point.yValue}`,
          },
          {
            field: "type",
            label: "Type",
          },
        ],
      },
    });
  }, [chartData, theme, isMobile, chartType]);

  useDocumentTitle(`History Statistics - ${useInstanceName()}`);

  const activeFilterCount = [action, provider, lang].filter(Boolean).length;

  const chartTypeIcons = {
    bar: faChartBar,
    line: faChartLine,
    area: faChartArea,
  };

  const chartTypeControl = (
    <Menu position="bottom-end" shadow="md" withinPortal>
      <Menu.Target>
        <Button
          variant="subtle"
          color="gray"
          size="xs"
          leftSection={
            <FontAwesomeIcon icon={chartTypeIcons[chartType]} size="lg" />
          }
          styles={{
            root: { height: "auto", padding: "6px 12px" },
            inner: { flexDirection: "column", gap: 6 },
            section: { marginInlineEnd: 0 },
          }}
          aria-label={`Chart type: ${chartType}`}
        >
          Chart
        </Button>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Item
          leftSection={<FontAwesomeIcon icon={faChartBar} />}
          rightSection={
            chartType === "bar" ? <FontAwesomeIcon icon={faCheck} /> : undefined
          }
          onClick={() => setChartType("bar")}
        >
          Bar chart
        </Menu.Item>
        <Menu.Item
          leftSection={<FontAwesomeIcon icon={faChartLine} />}
          rightSection={
            chartType === "line" ? (
              <FontAwesomeIcon icon={faCheck} />
            ) : undefined
          }
          onClick={() => setChartType("line")}
        >
          Line chart
        </Menu.Item>
        <Menu.Item
          leftSection={<FontAwesomeIcon icon={faChartArea} />}
          rightSection={
            chartType === "area" ? (
              <FontAwesomeIcon icon={faCheck} />
            ) : undefined
          }
          onClick={() => setChartType("area")}
        >
          Area chart
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );

  const filterControls = (
    <>
      <Selector
        placeholder="Time..."
        options={timeFrameOptions}
        value={timeFrame}
        onChange={(v) => setTimeFrame(v ?? "month")}
      ></Selector>
      <Selector
        placeholder="Action..."
        clearable
        options={actionOptions}
        value={action}
        onChange={setAction}
      ></Selector>
      <Selector
        {...providerOptions}
        placeholder="Provider..."
        clearable
        value={provider}
        onChange={setProvider}
      ></Selector>
      <Selector
        {...languageOptions}
        placeholder="Language..."
        clearable
        value={lang}
        onChange={setLanguage}
      ></Selector>
    </>
  );

  return (
    <Container fluid px={0} className={styles.container}>
      <QueryOverlay result={stats}>
        <Toolbox>
          <Group gap="xs" justify="space-between" wrap="nowrap">
            <Popover
              opened={filtersOpened}
              onChange={setFiltersOpened}
              position="bottom-start"
              withArrow
              shadow="md"
              withinPortal
            >
              <Popover.Target>
                <Indicator
                  disabled={activeFilterCount === 0}
                  label={activeFilterCount}
                  size={16}
                >
                  <Button
                    variant="subtle"
                    color="gray"
                    size="xs"
                    leftSection={<FontAwesomeIcon icon={faFilter} size="lg" />}
                    styles={{
                      root: { height: "auto", padding: "6px 12px" },
                      inner: { flexDirection: "column", gap: 6 },
                      section: { marginInlineEnd: 0 },
                    }}
                    aria-label="Filters"
                    onClick={() => setFiltersOpened((opened) => !opened)}
                  >
                    Filters
                  </Button>
                </Indicator>
              </Popover.Target>
              <Popover.Dropdown>
                <Stack gap="xs" w={260}>
                  {filterControls}
                </Stack>
              </Popover.Dropdown>
            </Popover>
            {chartTypeControl}
          </Group>
        </Toolbox>
        <Box className={styles.chart} m="xs">
          <Chart
            definition={definition}
            aspectRatio={isMobile ? 4 / 3 : 16 / 9}
            initialWidth={isMobile ? 400 : 720}
            ariaLabel="History statistics"
          />
        </Box>
      </QueryOverlay>
    </Container>
  );
};

export default HistoryStats;
