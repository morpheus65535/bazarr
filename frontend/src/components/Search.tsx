import { FunctionComponent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Autocomplete, ComboboxItem, OptionsFilter, Text } from "@mantine/core";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { chain, includes } from "lodash";
import { useServerSearch } from "@/apis/hooks";
import { useDebouncedValue } from "@/utilities";

type SearchResultItem = {
  value: string;
  link: string;
};

function useSearch(query: string) {
  const debouncedQuery = useDebouncedValue(query, 500);
  const { data } = useServerSearch(debouncedQuery, debouncedQuery.length >= 0);

  const duplicates = chain(data)
    .groupBy((item) => `${item.title} (${item.year})`)
    .filter((group) => group.length > 1)
    .map((group) => `${group[0].title} (${group[0].year})`)
    .value();

  return useMemo<SearchResultItem[]>(
    () =>
      data?.map((v) => {
        const { link, displayName } = (() => {
          const hasDuplicate = includes(duplicates, `${v.title} (${v.year})`);

          if (v.sonarrSeriesId) {
            return {
              link: `/series/${v.sonarrSeriesId}`,
              displayName: hasDuplicate
                ? `${v.title} (${v.year}) (S)`
                : `${v.title} (${v.year})`,
            };
          }

          if (v.radarrId) {
            return {
              link: `/movies/${v.radarrId}`,
              displayName: hasDuplicate
                ? `${v.title} (${v.year}) (M)`
                : `${v.title} (${v.year})`,
            };
          }

          throw new Error("Unknown search result");
        })();

        return {
          value: displayName,
          link,
        };
      }) ?? [],
    [data, duplicates],
  );
}

const optionsFilter: OptionsFilter = ({ options, search }) => {
  const lowercaseSearch = search.toLowerCase();
  const trimmedSearch = search.trim();

  return (options as ComboboxItem[]).filter((option) => {
    return (
      option.value.toLowerCase().includes(lowercaseSearch) ||
      option.value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .includes(trimmedSearch)
    );
  });
};

const Search: FunctionComponent = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const results = useSearch(query);

  return (
    <Autocomplete
      leftSection={<FontAwesomeIcon icon={faSearch} />}
      renderOption={(input) => <Text p="xs">{input.option.value}</Text>}
      placeholder="Search"
      size="sm"
      data={results}
      value={query}
      scrollAreaProps={{ type: "auto" }}
      maxDropdownHeight={400}
      onChange={setQuery}
      onBlur={() => setQuery("")}
      filter={optionsFilter}
      onOptionSubmit={(option) =>
        navigate(results.find((a) => a.value === option)?.link || "/")
      }
    ></Autocomplete>
  );
};

export default Search;
