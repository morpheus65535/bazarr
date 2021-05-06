interface ReduxStore {
  system: ReduxStore.System;
  series: ReduxStore.Series;
  movie: ReduxStore.Movie;
  site: ReduxStore.Site;
}

namespace ReduxStore {
  interface Notification {
    type: "error" | "warning" | "info";
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
    health: AsyncState<Array<System.Health>>;
    tasks: AsyncState<Array<System.Task>>;
    providers: AsyncState<Array<System.Provider>>;
    logs: AsyncState<Array<System.Log>>;
    releases: AsyncState<Array<ReleaseInfo>>;
    settings: AsyncState<Settings | undefined>;
  }

  interface Series {
    seriesList: AsyncOrderState<Item.Series>;
    wantedEpisodesList: AsyncOrderState<Wanted.Episode>;
    episodeList: AsyncState<Item.Episode[]>;
    historyList: AsyncState<Array<History.Episode>>;
    blacklist: AsyncState<Array<Blacklist.Episode>>;
  }

  interface Movie {
    movieList: AsyncOrderState<Item.Movie>;
    wantedMovieList: AsyncOrderState<Wanted.Movie>;
    historyList: AsyncState<Array<History.Movie>>;
    blacklist: AsyncState<Array<Blacklist.Movie>>;
  }
}
