import { useHistoryStats, useSystemProviders } from "@/apis/hooks";
import { ContentHeader, QueryOverlay, Selector } from "@/components";
import Language from "@/components/bazarr/Language";
import { merge } from "lodash";
import React, { FunctionComponent, useMemo, useState } from "react";
import { Col, Container } from "react-bootstrap";
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

const SelectorContainer: FunctionComponent = ({ children }) => (
  <Col xs={6} lg={3} className="p-1">
    {children}
  </Col>
);

const HistoryStats: FunctionComponent = () => {
  const { data: providers } = useSystemProviders(true);

  const providerOptions = useMemo<SelectorOption<System.Provider>[]>(
    () => providers?.map((value) => ({ label: value.name, value })) ?? [],
    [providers]
  );

  const [timeFrame, setTimeFrame] = useState<History.TimeFrameOptions>("month");
  const [action, setAction] = useState<Nullable<History.ActionOptions>>(null);
  const [lang, setLanguage] = useState<Nullable<Language.Info>>(null);
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
    // TODO: Responsive
    <Container fluid className="vh-75">
      <Helmet>
        <title>History Statistics - Bazarr</title>
      </Helmet>
      <QueryOverlay result={stats}>
        <React.Fragment>
          <ContentHeader scroll={false}>
            <SelectorContainer>
              <Selector
                placeholder="Time..."
                options={timeFrameOptions}
                value={timeFrame}
                onChange={(v) => setTimeFrame(v ?? "month")}
              ></Selector>
            </SelectorContainer>
            <SelectorContainer>
              <Selector
                placeholder="Action..."
                clearable
                options={actionOptions}
                value={action}
                onChange={setAction}
              ></Selector>
            </SelectorContainer>
            <SelectorContainer>
              <Selector
                placeholder="Provider..."
                clearable
                options={providerOptions}
                value={provider}
                onChange={setProvider}
              ></Selector>
            </SelectorContainer>
            <SelectorContainer>
              <Language.Selector
                clearable
                value={lang}
                onChange={setLanguage}
                history
              ></Language.Selector>
            </SelectorContainer>
          </ContentHeader>
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
        </React.Fragment>
      </QueryOverlay>
    </Container>
  );
};

export default HistoryStats;
