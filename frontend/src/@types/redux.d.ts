interface ReduxStore {
  badges: ReduxStore.Badge;
  system: ReduxStore.System;
  series: ReduxStore.Series;
  movie: ReduxStore.Movie;
  site: ReduxStore.Site;
}

namespace ReduxStore {
  interface Site {
    initialized: boolean;
    auth: boolean;
    pageSize: number;
  }

  interface Badge {
    movies: number;
    episodes: number;
    providers: number;
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
    [key: number]: Array<Item.Episode>;
  }

  interface Series {
    seriesList: AsyncState<Array<Item.Series>>;
    wantedSeriesList: AsyncState<Array<Wanted.Episode>>;
    episodeList: AsyncState<EpisodeState>;
    historyList: AsyncState<Array<History.Episode>>;
    blacklist: AsyncState<Array<Blacklist.Episode>>;
  }

  interface Movie {
    movieList: AsyncState<Array<Item.Movie>>;
    historyList: AsyncState<Array<History.Movie>>;
    blacklist: AsyncState<Array<Blacklist.Movie>>;
  }
}
