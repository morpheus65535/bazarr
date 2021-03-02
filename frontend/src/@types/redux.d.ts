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
    languagesProfiles: AsyncState<Array<LanguagesProfile>>;
    status: AsyncState<SystemStatusResult | undefined>;
    tasks: AsyncState<Array<SystemTaskResult>>;
    providers: AsyncState<Array<SystemProvider>>;
    logs: AsyncState<Array<SystemLog>>;
    releases: AsyncState<Array<ReleaseInfo>>;
    settings: AsyncState<Settings | undefined>;
  }

  interface Series {
    seriesList: AsyncState<Array<Item.Series>>;
    wantedSeriesList: AsyncState<Array<Wanted.Episode>>;
    episodeList: AsyncState<Map<number, Array<Item.Episode>>>;
    historyList: AsyncState<Array<History.Episode>>;
    blacklist: AsyncState<Array<Blacklist.Episode>>;
  }

  interface Movie {
    movieList: AsyncState<Array<Item.Movie>>;
    wantedMovieList: AsyncState<Array<Wanted.Movie>>;
    historyList: AsyncState<Array<History.Movie>>;
    blacklist: AsyncState<Array<Blacklist.Movie>>;
  }
}
