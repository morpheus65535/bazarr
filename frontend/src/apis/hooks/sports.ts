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

const cacheLeagues = (client: QueryClient, leagues: Item.SportsLeague[]) => {
  leagues.forEach((item) => {
    client.setQueryData([QueryKeys.SportsLeagues, item.sportarrLeagueId], item);
  });
};

export const useSportsLeagueById = (id: number) => {
  return useQuery({
    queryKey: [QueryKeys.SportsLeagues, id],

    queryFn: async () => {
      const response = await api.sports.leagues([id]);
      return response.length > 0 ? response[0] : undefined;
    },
  });
};

export const useSportsLeagues = (state: Parameter.ListState = {}) => {
  const client = useQueryClient();

  const query = useQuery({
    queryKey: [QueryKeys.SportsLeagues, QueryKeys.All, state],
    queryFn: async () => {
      const response = await api.sports.leaguesBy({
        start: 0,
        length: -1,
        ...state,
      });
      return response.data;
    },
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      cacheLeagues(client, query.data);
    }
  }, [query.isSuccess, query.data, client]);

  return query;
};

export const sportsLeaguesPaginationKey = [QueryKeys.SportsLeagues];

export const sportsLeaguesPaginationQuery: RangeQuery<Item.SportsLeague> = (
  param,
) => api.sports.leaguesBy(param);

export const useSportsLeagueModification = () => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.SportsLeagues],
    mutationFn: (form: FormType.ModifyItem) => api.sports.modifyLeague(form),

    onSuccess: (_, form) => {
      form.id.forEach((v) => {
        void client.invalidateQueries({
          queryKey: [QueryKeys.SportsLeagues, v],
        });
      });
      void client.invalidateQueries({
        queryKey: [QueryKeys.SportsLeagues],
      });
    },
  });
};

export const useSportsLeagueAction = () => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Actions, QueryKeys.SportsLeagues],
    mutationFn: (form: FormType.SportsLeagueAction) =>
      api.sports.leagueAction(form),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.SportsLeagues],
      });
    },
  });
};

export const useSportsEventsByLeagueId = (leagueId?: number) =>
  useQuery({
    queryKey: [QueryKeys.SportsLeagues, leagueId, QueryKeys.SportsEvents],

    queryFn: () => {
      if (leagueId) {
        return api.sports.byLeagueId([leagueId]);
      }

      return [];
    },
  });

export const useSportsEventsById = (eventIds: number[]) =>
  useQuery({
    queryKey: [QueryKeys.SportsEvents, ...eventIds],
    queryFn: () => api.sports.byEventId(eventIds),
  });

export const useSportsWantedPagination = () =>
  usePaginationQuery(
    [QueryKeys.SportsLeagues, QueryKeys.SportsEvents, QueryKeys.Wanted],
    (param) => api.sports.wanted(param),
  );

export const useSportsBlacklist = () =>
  useQuery({
    queryKey: [
      QueryKeys.SportsLeagues,
      QueryKeys.SportsEvents,
      QueryKeys.Blacklist,
    ],
    queryFn: () => api.sports.blacklist(),
  });

export const useSportsAddBlacklist = () => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [
      QueryKeys.SportsLeagues,
      QueryKeys.SportsEvents,
      QueryKeys.Blacklist,
    ],

    mutationFn: (param: {
      leagueId: number;
      eventId: number;
      form: FormType.AddBlacklist;
    }) => {
      const { leagueId, eventId, form } = param;
      return api.sports.addBlacklist(leagueId, eventId, form);
    },

    onSuccess: (_, { leagueId }) => {
      void client.invalidateQueries({
        queryKey: [
          QueryKeys.SportsLeagues,
          QueryKeys.SportsEvents,
          QueryKeys.Blacklist,
        ],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.SportsLeagues, leagueId],
      });
    },
  });
};

export const useSportsDeleteBlacklist = () => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [
      QueryKeys.SportsLeagues,
      QueryKeys.SportsEvents,
      QueryKeys.Blacklist,
    ],

    mutationFn: (param: { all?: boolean; form?: FormType.DeleteBlacklist }) =>
      api.sports.deleteBlacklist(param.all, param.form),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [
          QueryKeys.SportsLeagues,
          QueryKeys.SportsEvents,
          QueryKeys.Blacklist,
        ],
      });
    },
  });
};

export const useSportsHistoryPagination = () =>
  usePaginationQuery(
    [QueryKeys.SportsLeagues, QueryKeys.SportsEvents, QueryKeys.History],
    (param) => api.sports.history(param),
    false,
  );

export const useSportsHistory = (eventId?: number) =>
  useQuery({
    queryKey: [
      QueryKeys.SportsLeagues,
      QueryKeys.SportsEvents,
      QueryKeys.History,
      eventId,
    ],

    queryFn: () => {
      if (eventId) {
        return api.sports.historyBy(eventId);
      }

      return [];
    },
  });
