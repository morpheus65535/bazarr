import {
  useHistoryStats,
  useLanguages,
  useSystemProviders,
} from "@/apis/hooks";
import { Selector, Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import Language from "@/components/bazarr/Language";
import { useSelectorOptions } from "@/utilities";
import { Container, Grid, Stack } from "@mantine/core";
import { merge } from "lodash";
import { FunctionComponent, useMemo, useState } from "react";
import { Helmet } from "react-helmet";
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
import { actionOptions, timeFrameOptions } from "./options";

const HistoryStats: FunctionComponent = () => {
  const { data: providers } = useSystemProviders(true);

  const providerOptions = useSelectorOptions(providers ?? [], (v) => v.name);

  const { data: historyLanguages } = useLanguages(true);

  const languageOptions = useSelectorOptions(
    historyLanguages ?? [],
    (value) => value.name
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
      const result = merge(movies, series);
      return result;
    } else {
      return [];
    }
  }, [data]);

  return (
    <Container fluid px={0}>
      <Helmet>
        <title>History Statistics - Bazarr</title>
      </Helmet>
      <QueryOverlay result={stats}>
        <Stack>
          <Toolbox>
            <Grid grow>
              <Grid.Col span={3}>
                <Selector
                  placeholder="Time..."
                  options={timeFrameOptions}
                  value={timeFrame}
                  onChange={(v) => setTimeFrame(v ?? "month")}
                ></Selector>
              </Grid.Col>
              <Grid.Col span={3}>
                <Selector
                  placeholder="Action..."
                  clearable
                  options={actionOptions}
                  value={action}
                  onChange={setAction}
                ></Selector>
              </Grid.Col>
              <Grid.Col span={3}>
                <Selector
                  {...providerOptions}
                  placeholder="Provider..."
                  clearable
                  value={provider}
                  onChange={setProvider}
                ></Selector>
              </Grid.Col>
              <Grid.Col span={3}>
                <Selector
                  {...languageOptions}
                  clearable
                  value={lang}
                  onChange={setLanguage}
                ></Selector>
              </Grid.Col>
            </Grid>
          </Toolbox>
          <ResponsiveContainer height="100%">
            <BarChart data={convertedData}>
              <CartesianGrid strokeDasharray="4 2"></CartesianGrid>
              <XAxis dataKey="date"></XAxis>
              <YAxis allowDecimals={false}></YAxis>
              <Tooltip></Tooltip>
              <Legend verticalAlign="top"></Legend>
              <Bar name="Series" dataKey="series" fill="#2493B6"></Bar>
              <Bar name="Movies" dataKey="movies" fill="#FFC22F"></Bar>
            </BarChart>
          </ResponsiveContainer>
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

export default HistoryStats;
