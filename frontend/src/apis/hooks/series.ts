import { useEffect } from "react";
import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { usePaginationQuery } from "@/apis/queries/hooks";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

function cacheSeries(client: QueryClient, series: Item.Series[]) {
  series.forEach((item) => {
    client.setQueryData([QueryKeys.Series, item.sonarrSeriesId], item);
  });
}

export function useSeriesByIds(ids: number[]) {
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
}

export function useSeriesById(id: number) {
  return useQuery({
    queryKey: [QueryKeys.Series, id],

    queryFn: async () => {
      const response = await api.series.series([id]);
      return response.length > 0 ? response[0] : undefined;
    },
  });
}

export function useSeries() {
  const client = useQueryClient();

  const query = useQuery({
    queryKey: [QueryKeys.Series, QueryKeys.All],
    queryFn: () => api.series.series(),
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      cacheSeries(client, query.data);
    }
  }, [query.isSuccess, query.data, client]);

  return query;
}

export function useSeriesPagination() {
  return usePaginationQuery([QueryKeys.Series], (param) =>
    api.series.seriesBy(param),
  );
}

export function useSeriesModification() {
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
}

export function useSeriesAction() {
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
}
