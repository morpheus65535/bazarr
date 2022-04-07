import { QueryKeys } from "@/apis/queries/keys";
import {
  hideNotification,
  showNotification,
  updateNotification,
} from "@mantine/notifications";
import queryClient from "../../apis/queries";
import { notification } from "../notifications";
import { setOfflineStatus, setSiteStatus } from "../redux/actions";
import { AnyActionCreator } from "../redux/actions/types";
import reduxStore from "../redux/store";

function bindReduxActionWithParam<T extends AnyActionCreator>(
  action: T,
  ...param: Parameters<T>
) {
  return () => {
    reduxStore.dispatch(action(...param));
  };
}

export function createDefaultReducer(): SocketIO.Reducer[] {
  return [
    {
      key: "connect",
      any: bindReduxActionWithParam(setOfflineStatus, false),
    },
    {
      key: "connect",
      any: () => {
        // init
        reduxStore.dispatch(setSiteStatus("initialized"));
      },
    },
    {
      key: "connect_error",
      any: () => {
        reduxStore.dispatch(setSiteStatus("error"));
      },
    },
    {
      key: "disconnect",
      any: bindReduxActionWithParam(setOfflineStatus, true),
    },
    {
      key: "message",
      update: (msg) => {
        msg
          .map((message) => notification.info("Notification", message))
          .forEach(showNotification);
      },
    },
    {
      key: "progress",
      update: (progress) => {
        progress.forEach((item) => {
          const props = notification.progress(
            item.id,
            item.header,
            item.name,
            item.value + 1,
            item.count
          );

          if (item.value === 0) {
            showNotification(props);
          } else {
            updateNotification(props);
          }
        });
      },
      delete: (ids) => {
        setTimeout(
          () => ids.forEach(hideNotification),
          notification.PROGRESS_TIMEOUT
        );
      },
    },
    {
      key: "series",
      update: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Series, id]);
        });
      },
      delete: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Series, id]);
        });
      },
    },
    {
      key: "movie",
      update: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Movies, id]);
        });
      },
      delete: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Movies, id]);
        });
      },
    },
    {
      key: "episode",
      update: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Episodes, id]);
        });
      },
      delete: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Episodes, id]);
        });
      },
    },
    {
      key: "episode-wanted",
      update: (ids) => {
        // Find a better way to update wanted
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.Wanted]);
      },
      delete: () => {
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.Wanted]);
      },
    },
    {
      key: "movie-wanted",
      update: (ids) => {
        // Find a better way to update wanted
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
      },
      delete: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
      },
    },
    {
      key: "settings",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System]);
      },
    },
    {
      key: "languages",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System, QueryKeys.Languages]);
      },
    },
    {
      key: "badges",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System, QueryKeys.Badges]);
      },
    },
    {
      key: "movie-history",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.History]);
      },
    },
    {
      key: "movie-blacklist",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Blacklist]);
      },
    },
    {
      key: "episode-history",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.History]);
      },
    },
    {
      key: "episode-blacklist",
      any: () => {
        queryClient.invalidateQueries([
          QueryKeys.Episodes,
          QueryKeys.Blacklist,
        ]);
      },
    },
    {
      key: "reset-episode-wanted",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.Wanted]);
      },
    },
    {
      key: "reset-movie-wanted",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
      },
    },
    {
      key: "task",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System, QueryKeys.Tasks]);
      },
    },
  ];
}
