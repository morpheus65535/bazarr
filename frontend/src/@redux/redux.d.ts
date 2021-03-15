interface IdState<T> {
  [key: number]: Readonly<T>;
}

interface OrderIdState<T> {
  items: IdState<T>;
  order: (number | null)[];
}

interface ReduxStore {
  system: ReduxStore.System;
  series: ReduxStore.Series;
  movie: ReduxStore.Movie;
  site: ReduxStore.Site;
}

namespace ReduxStore {
  interface Notification {
    type: "error" | "warning";
    message: string;
    timestamp: Date;
    id: string;
  }

  interface Site {
    // Initialization state or error message
    initialized: boolean | string;
    auth: boolean;
    pageSize: number;
    notifications: Notification[];
    sidebar: string;
    badges: Badge;
    offline: boolean;
  }

  interface System {
    languages: AsyncState<Array<Language>>;
    enabledLanguage: AsyncState<Array<Language>>;
    languagesProfiles: AsyncState<Array<Profile.Languages>>;
    status: AsyncState<System.Status | undefined>;
    tasks: AsyncState<Array<System.Task>>;
    providers: AsyncState<Array<System.Provider>>;
    logs: AsyncState<Array<System.Log>>;
    releases: AsyncState<Array<ReleaseInfo>>;
    settings: AsyncState<Settings | undefined>;
  }

  interface Series {
    seriesList: AsyncState<OrderIdState<Item.Series>>;
    wantedSeriesList: AsyncState<Array<Wanted.Episode>>;
    episodeList: AsyncState<IdState<Item.Episode[]>>;
    historyList: AsyncState<Array<History.Episode>>;
    blacklist: AsyncState<Array<Blacklist.Episode>>;
  }

  interface Movie {
    movieList: AsyncState<OrderIdState<Item.Movie>>;
    historyList: AsyncState<Array<History.Movie>>;
    blacklist: AsyncState<Array<Blacklist.Movie>>;
  }
}
