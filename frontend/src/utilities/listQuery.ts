import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";

interface ListQueryKeys {
  sortBy: string;
  sortOrder: string;
  monitored: string;
  missing: string;
  profileId: string;
  audioLanguage: string;
  tags: string;
}

// URL params are optionally scoped with a page prefix (e.g. "series_sort_by")
// so filter/sort state does not bleed between the series and movies pages.
const keysFor = (prefix?: string): ListQueryKeys => {
  const p = prefix ? `${prefix}_` : "";
  return {
    sortBy: `${p}sort_by`,
    sortOrder: `${p}sort_order`,
    monitored: `${p}monitored`,
    missing: `${p}missing`,
    profileId: `${p}profileid`,
    audioLanguage: `${p}audio_language`,
    tags: `${p}tags`,
  };
};

// A profileId of 0 means "items without a languages profile", sent to the
// backend as "none".
const NO_PROFILE = "none";

export const parseListQuery = (
  searchParams: URLSearchParams,
  prefix?: string,
): Parameter.ListState => {
  const keys = keysFor(prefix);

  const sortBy = searchParams.get(keys.sortBy) ?? undefined;
  const sortOrder =
    (searchParams.get(keys.sortOrder) as "asc" | "desc" | null) ?? undefined;

  const filters: Parameter.ListFilters = {};
  const monitored = searchParams.get(keys.monitored);
  const missing = searchParams.get(keys.missing);
  const profileId = searchParams.get(keys.profileId);
  const tags = searchParams.getAll(keys.tags);

  if (monitored !== null) {
    filters.monitored = monitored === "true";
  }
  if (missing !== null) {
    filters.missing = missing === "true";
  }
  if (profileId !== null) {
    filters.profileId = profileId === NO_PROFILE ? 0 : Number(profileId);
  }
  const audioLanguage = searchParams.get(keys.audioLanguage);
  if (audioLanguage !== null) {
    filters.audioLanguage = audioLanguage;
  }
  if (tags.length > 0) {
    filters.tags = tags;
  }

  return {
    sortBy,
    sortOrder,
    filters: Object.keys(filters).length > 0 ? filters : undefined,
  };
};

const setOrDelete = (
  params: URLSearchParams,
  key: string,
  value: string | undefined,
) => {
  if (value === undefined) {
    params.delete(key);
    return;
  }
  params.set(key, value);
};

const boolParam = (value: boolean | undefined) =>
  value === undefined ? undefined : value ? "true" : "false";

export const buildListSearchParams = (
  searchParams: URLSearchParams,
  query: Parameter.ListState,
  prefix?: string,
): URLSearchParams => {
  const keys = keysFor(prefix);
  const next = new URLSearchParams(searchParams);

  setOrDelete(next, keys.sortBy, query.sortBy);
  setOrDelete(next, keys.sortOrder, query.sortOrder);
  setOrDelete(next, keys.monitored, boolParam(query.filters?.monitored));
  setOrDelete(next, keys.missing, boolParam(query.filters?.missing));
  setOrDelete(
    next,
    keys.profileId,
    query.filters?.profileId === undefined
      ? undefined
      : query.filters.profileId === 0
        ? NO_PROFILE
        : String(query.filters.profileId),
  );
  setOrDelete(next, keys.audioLanguage, query.filters?.audioLanguage);

  next.delete(keys.tags);
  if (query.filters?.tags && query.filters.tags.length > 0) {
    query.filters.tags.forEach((tag) => next.append(keys.tags, tag));
  }

  return next;
};

export const useListQueryState = (prefix?: string) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = useMemo(
    () => parseListQuery(searchParams, prefix),
    [searchParams, prefix],
  );

  const update = useCallback(
    (nextQuery: Parameter.ListState) => {
      const next = buildListSearchParams(searchParams, nextQuery, prefix);
      next.delete("page");
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams, prefix],
  );

  const setSort = useCallback(
    (sortBy: string, sortOrder: "asc" | "desc") => {
      update({ ...query, sortBy, sortOrder });
    },
    [query, update],
  );

  const setFilter = useCallback(
    <K extends keyof Parameter.ListFilters>(
      key: K,
      value: Parameter.ListFilters[K] | undefined,
    ) => {
      const filters: Parameter.ListFilters = { ...query.filters };

      const shouldRemove =
        value === undefined || (Array.isArray(value) && value.length === 0);

      if (shouldRemove) {
        delete filters[key];
      }
      if (!shouldRemove) {
        filters[key] = value;
      }

      update({
        ...query,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
      });
    },
    [query, update],
  );

  const clearFilters = useCallback(() => {
    update({ sortBy: query.sortBy, sortOrder: query.sortOrder });
  }, [query, update]);

  return { query, setSort, setFilter, clearFilters };
};
