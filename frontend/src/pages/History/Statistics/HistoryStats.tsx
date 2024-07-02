import { FunctionComponent, useMemo, useState } from "react";
import { Box, Container, SimpleGrid, useMantineTheme } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { merge } from "lodash";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  useHistoryStats,
  useLanguages,
  useSystemProviders,
} from "@/apis/hooks";
import { Selector, Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { useSelectorOptions } from "@/utilities";
import { actionOptions, timeFrameOptions } from "./options";
import styles from "./HistoryStats.module.scss";

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

  const stats = useHistoryStats(timeFrame, action, provider, lang);
  const { data } = stats;

  const convertedData = useMemo(() => {
    if (data) {
      const movies = data.movies.map((v) => ({
        date: v.date,
        movies: v.count,
      }));
      const series = data.series.map((v) => ({
        date: v.date,
        series: v.count,
      }));

      return merge(movies, series);
    } else {
      return [];
    }
  }, [data]);

  useDocumentTitle("History Statistics - Bazarr");

  const theme = useMantineTheme();

  return (
    <Container fluid px={0} className={styles.container}>
      <QueryOverlay result={stats}>
        <Toolbox>
          <SimpleGrid cols={{ base: 4, xs: 2 }}>
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
          </SimpleGrid>
        </Toolbox>
        <Box className={styles.chart} m="xs">
          <ResponsiveContainer>
            <BarChart className={styles.chart} data={convertedData}>
              <CartesianGrid strokeDasharray="4 2"></CartesianGrid>
              <XAxis dataKey="date"></XAxis>
              <YAxis allowDecimals={false}></YAxis>
              <Tooltip></Tooltip>
              <Legend verticalAlign="top"></Legend>
              <Bar
                name="Series"
                dataKey="series"
                fill={theme.colors.blue[4]}
              ></Bar>
              <Bar
                name="Movies"
                dataKey="movies"
                fill={theme.colors.yellow[4]}
              ></Bar>
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </QueryOverlay>
    </Container>
  );
};

export default HistoryStats;
