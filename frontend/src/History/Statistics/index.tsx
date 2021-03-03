import { merge } from "lodash";
import React, { FunctionComponent, useCallback, useState } from "react";
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
import { HistoryApi } from "../../apis";
import {
  AsyncSelector,
  ContentHeader,
  LanguageSelector,
  PromiseOverlay,
  Selector,
} from "../../components";
import { useLanguages } from "../../utilites";
import { useProviders } from "../../utilites/items";
import { actionOptions, timeframeOptions } from "./options";

function converter(item: History.Stat) {
  const movies = item.movies.map((v) => ({
    date: v.date,
    movies: v.count,
  }));
  const series = item.series.map((v) => ({
    date: v.date,
    series: v.count,
  }));
  const result = merge(movies, series);
  return result;
}

const providerLabel = (item: System.Provider) => item.name;

const SelectorContainer: FunctionComponent = ({ children }) => (
  <Col xs={6} lg={3} className="p-1">
    {children}
  </Col>
);

const HistoryStats: FunctionComponent = () => {
  const languages = useLanguages(true);

  const providerList = useProviders();

  const [timeframe, setTimeframe] = useState<History.TimeframeOptions>("month");
  const [action, setAction] = useState<History.ActionOptions | undefined>(
    undefined
  );
  const [lang, setLanguage] = useState<Language | undefined>(undefined);
  const [provider, setProvider] = useState<System.Provider | undefined>(
    undefined
  );

  const promise = useCallback(() => {
    return HistoryApi.stats(timeframe, action, provider?.name, lang?.code2);
  }, [timeframe, lang?.code2, action, provider]);

  return (
    // TODO: Responsive
    <Container fluid className="vh-75">
      <Helmet>
        <title>History Statistics - Bazarr</title>
      </Helmet>
      <PromiseOverlay promise={promise}>
        {(data) => (
          <React.Fragment>
            <ContentHeader scroll={false}>
              <SelectorContainer>
                <Selector
                  placeholder="Time..."
                  options={timeframeOptions}
                  value={timeframe}
                  onChange={(v) => setTimeframe(v ?? "month")}
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
                <AsyncSelector
                  placeholder="Provider..."
                  clearable
                  state={providerList}
                  label={providerLabel}
                  onChange={setProvider}
                ></AsyncSelector>
              </SelectorContainer>
              <SelectorContainer>
                <LanguageSelector
                  clearable
                  options={languages}
                  value={lang}
                  onChange={setLanguage}
                ></LanguageSelector>
              </SelectorContainer>
            </ContentHeader>
            <ResponsiveContainer height="100%">
              <BarChart data={converter(data)}>
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
        )}
      </PromiseOverlay>
    </Container>
  );
};

export default HistoryStats;
