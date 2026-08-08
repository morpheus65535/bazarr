import { useEffect } from "react";
import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

const cacheSeries = (client: QueryClient, series: Item.Series[]) => {
  series.forEach((item) => {
    client.setQueryData([QueryKeys.Series, item.sonarrSeriesId], item);
  });
};

export const useSeriesByIds = (ids: number[]) => {
  const client = useQueryClient();

  const query = useQuery({
    queryKey: [QueryKeys.Series, ...ids],
    queryFn: () => api.series.series(ids),
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      cacheSeries(client, query.data);
    }
  }, [query.isSuccess, query.data, client]);

  return query;
};

export const useSeriesById = (id: number) => {
  return useQuery({
    queryKey: [QueryKeys.Series, id],

    queryFn: async () => {
      const response = await api.series.series([id]);
      return response.length > 0 ? response[0] : undefined;
    },
  });
};

export const useSeries = (state: Parameter.ListState = {}) => {
  const client = useQueryClient();

  const query = useQuery({
    queryKey: [QueryKeys.Series, QueryKeys.All, state],
    queryFn: async () => {
      const response = await api.series.seriesBy({
        start: 0,
        length: -1,
        ...state,
      });
      return response.data;
    },
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      cacheSeries(client, query.data);
    }
  }, [query.isSuccess, query.data, client]);

  return query;
};

export const seriesPaginationKey = [QueryKeys.Series];

export const seriesPaginationQuery: RangeQuery<Item.Series> = (param) =>
  api.series.seriesBy(param);

export const useSeriesModification = () => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Series],
    mutationFn: (form: FormType.ModifyItem) => api.series.modify(form),

    onSuccess: (_, form) => {
      form.id.forEach((v) => {
        client.invalidateQueries({
          queryKey: [QueryKeys.Series, v],
        });
      });
      client.invalidateQueries({
        queryKey: [QueryKeys.Series],
      });
    },
  });
};

export const useSeriesAction = () => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Actions, QueryKeys.Series],
    mutationFn: (form: FormType.SeriesAction) => api.series.action(form),

    onSuccess: () => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Series],
      });
    },
  });
};
