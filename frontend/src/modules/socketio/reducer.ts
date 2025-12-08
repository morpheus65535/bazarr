import { cleanNotifications, showNotification } from "@mantine/notifications";
import { isArray, isEmpty, isNumber } from "lodash";
import queryClient from "@/apis/queries";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import { notification } from "@/modules/task";
import { LOG } from "@/utilities/console";
import { setCriticalError, setOnlineStatus } from "@/utilities/event";

export function createDefaultReducer(): SocketIO.Reducer[] {
  return [
    {
      key: "connect",
      any: () => setOnlineStatus(true),
    },
    {
      key: "connect_error",
      any: () => {
        setCriticalError("Cannot connect to backend");
        cleanNotifications();
      },
    },
    {
      key: "disconnect",
      any: () => setOnlineStatus(false),
    },
    {
      key: "message",
      update: (msg) => {
        msg
          .map((message) => notification.info("Notification", message))
          .forEach((data) => showNotification(data));
      },
    },
    {
      key: "series",
      update: (ids) => {
        LOG("info", "Invalidating series", ids);
        ids.forEach((id) => {
          void queryClient.invalidateQueries({
            queryKey: [QueryKeys.Series, id],
          });
        });
      },
      delete: (ids) => {
        LOG("info", "Invalidating series", ids);
        ids.forEach((id) => {
          void queryClient.invalidateQueries({
            queryKey: [QueryKeys.Series, id],
          });
        });
      },
    },
    {
      key: "movie",
      update: (ids) => {
        LOG("info", "Invalidating movies", ids);
        ids.forEach((id) => {
          void queryClient.invalidateQueries({
            queryKey: [QueryKeys.Movies, id],
          });
        });
      },
      delete: (ids) => {
        LOG("info", "Invalidating movies", ids);
        ids.forEach((id) => {
          void queryClient.invalidateQueries({
            queryKey: [QueryKeys.Movies, id],
          });
        });
      },
    },
    {
      key: "episode",
      update: (ids) => {
        // Currently invalidate episodes is impossible because we don't directly fetch episodes (we fetch episodes by series id)
        // So we need to invalidate series instead
        // TODO: Make a query for episodes and invalidate that instead
        LOG("info", "Invalidating episodes", ids);
        ids.forEach((id) => {
          const episode = queryClient.getQueryData<Item.Episode>([
            QueryKeys.Episodes,
            id,
          ]);
          if (episode !== undefined) {
            void queryClient.invalidateQueries({
              queryKey: [QueryKeys.Series, episode.sonarrSeriesId],
            });
          }
        });
      },
      delete: (ids) => {
        LOG("info", "Invalidating episodes", ids);
        ids.forEach((id) => {
          const episode = queryClient.getQueryData<Item.Episode>([
            QueryKeys.Episodes,
            id,
          ]);
          if (episode !== undefined) {
            void queryClient.invalidateQueries({
              queryKey: [QueryKeys.Series, episode.sonarrSeriesId],
            });
          }
        });
      },
    },
    {
      key: "episode-wanted",
      update: () => {
        // Find a better way to update wanted
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Episodes, QueryKeys.Wanted],
        });
      },
      delete: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Episodes, QueryKeys.Wanted],
        });
      },
    },
    {
      key: "movie-wanted",
      update: () => {
        // Find a better way to update wanted
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Movies, QueryKeys.Wanted],
        });
      },
      delete: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Movies, QueryKeys.Wanted],
        });
      },
    },
    {
      key: "settings",
      any: () => {
        void queryClient.invalidateQueries({ queryKey: [QueryKeys.System] });
      },
    },
    {
      key: "languages",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.System, QueryKeys.Languages],
        });
      },
    },
    {
      key: "badges",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.System, QueryKeys.Badges],
        });
      },
    },
    {
      key: "movie-history",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Movies, QueryKeys.History],
        });
      },
    },
    {
      key: "movie-blacklist",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Movies, QueryKeys.Blacklist],
        });
      },
    },
    {
      key: "episode-history",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Episodes, QueryKeys.History],
        });
      },
    },
    {
      key: "episode-blacklist",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Episodes, QueryKeys.Blacklist],
        });
      },
    },
    {
      key: "reset-episode-wanted",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Episodes, QueryKeys.Wanted],
        });
      },
    },
    {
      key: "reset-movie-wanted",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.Movies, QueryKeys.Wanted],
        });
      },
    },
    {
      key: "task",
      any: () => {
        void queryClient.invalidateQueries({
          queryKey: [QueryKeys.System, QueryKeys.Tasks],
        });
      },
    },
    {
      key: "jobs",
      update: (items) => {
        const keys = [QueryKeys.System, QueryKeys.Jobs];
        const MAX_JOBS_IN_CACHE = 100;

        items.forEach((payload) => {
          // Payload is always a JSON string:
          // {"job_id": <number>, "progress_value": <number|null>, "progress_message": <string>, "status": <string>}
          // If progress_value is present (not null/undefined), apply (with progress_message and status) directly to
          // cache without an API call
          if (isNumber(payload.progress_value)) {
            const current = queryClient.getQueryData<LooseObject[]>(keys) || [];
            const idx = current.findIndex((j) => j.job_id === payload.job_id);

            const initialJob =
              // eslint-disable-next-line camelcase
              idx >= 0 ? { ...current[idx] } : { job_id: payload.job_id };

            const updatedJob = {
              ...initialJob,
              status: payload.status,
              /* eslint-disable camelcase */
              progress_value: payload.progress_value,
              progress_max: payload.progress_max,
              progress_message: payload.progress_message,
              /* eslint-enable camelcase */
            };

            const next =
              idx >= 0
                ? [
                    ...current.slice(0, idx),
                    updatedJob,
                    ...current.slice(idx + 1),
                  ]
                : [...current, updatedJob];

            // Prevent memory leak: keep only the most recent jobs
            const trimmed =
              next.length > MAX_JOBS_IN_CACHE
                ? next.slice(-MAX_JOBS_IN_CACHE)
                : next;

            queryClient.setQueryData(keys, trimmed);
            LOG(
              "info",
              "Applied inline payload content to cache",
              payload.job_id,
            );
            return;
          }

          // progress_value is null/undefined -> refresh this job via API
          LOG(
            "info",
            "progress_value missing; fetching job from API",
            payload.job_id,
          );
          void api.system
            .jobs(payload.job_id)
            .then((resp: LooseObject[] | undefined) => {
              const incomingJobs = isArray(resp) ? resp : [];
              if (isEmpty(incomingJobs)) {
                return;
              }
              const incoming = incomingJobs[0];

              const current =
                queryClient.getQueryData<LooseObject[]>(keys) || [];

              const idx = current.findIndex(
                (j) => j.job_id === incoming.job_id,
              );
              const next =
                idx >= 0
                  ? [
                      ...current.slice(0, idx),
                      { ...current[idx], ...incoming },
                      ...current.slice(idx + 1),
                    ]
                  : [...current, incoming];

              // Prevent memory leak: keep only the most recent jobs
              const trimmed =
                next.length > MAX_JOBS_IN_CACHE
                  ? next.slice(-MAX_JOBS_IN_CACHE)
                  : next;

              queryClient.setQueryData(keys, trimmed);
            })
            .catch((e: unknown) => {
              LOG("warning", "Failed to fetch job update", payload.job_id, e);
            });
        });
      },
    },
  ];
}
