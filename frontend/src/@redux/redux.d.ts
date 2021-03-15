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

  interface EpisodeState {
    [key: number]: readonly Item.Episode[];
  }

  interface Series {
    seriesList: AsyncState<Nullable<Item.Series>[]>;
    wantedSeriesList: AsyncState<Array<Wanted.Episode>>;
    episodeList: AsyncState<EpisodeState>;
    historyList: AsyncState<Array<History.Episode>>;
    blacklist: AsyncState<Array<Blacklist.Episode>>;
  }

  interface Movie {
    movieList: AsyncState<Nullable<Item.Movie>[]>;
    historyList: AsyncState<Array<History.Movie>>;
    blacklist: AsyncState<Array<Blacklist.Movie>>;
  }
}
