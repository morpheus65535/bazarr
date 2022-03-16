import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "react-query";
import { usePaginationQuery } from "../queries/hooks";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

function cacheSeries(client: QueryClient, series: Item.Series[]) {
  series.forEach((item) => {
    client.setQueryData([QueryKeys.Series, item.sonarrSeriesId], item);
  });
}

export function useSeriesByIds(ids: number[]) {
  const client = useQueryClient();
  return useQuery([QueryKeys.Series, ...ids], () => api.series.series(ids), {
    onSuccess: (data) => {
      cacheSeries(client, data);
    },
  });
}

export function useSeriesById(id: number) {
  return useQuery([QueryKeys.Series, id], async () => {
    const response = await api.series.series([id]);
    return response.length > 0 ? response[0] : undefined;
  });
}

export function useSeries() {
  const client = useQueryClient();
  return useQuery(
    [QueryKeys.Series, QueryKeys.All],
    () => api.series.series(),
    {
      onSuccess: (data) => {
        cacheSeries(client, data);
      },
    }
  );
}

export function useSeriesPagination() {
  return usePaginationQuery([QueryKeys.Series], (param) =>
    api.series.seriesBy(param)
  );
}

export function useSeriesModification() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Series],
    (form: FormType.ModifyItem) => api.series.modify(form),
    {
      onSuccess: (_, form) => {
        form.id.forEach((v) => {
          client.invalidateQueries([QueryKeys.Series, v]);
        });
        client.invalidateQueries([QueryKeys.Series]);
      },
    }
  );
}

export function useSeriesAction() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Actions, QueryKeys.Series],
    (form: FormType.SeriesAction) => api.series.action(form),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.Series]);
      },
    }
  );
}
