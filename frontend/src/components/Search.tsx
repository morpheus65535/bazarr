import { FunctionComponent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ComboboxItem,
  Image,
  OptionsFilter,
  Select,
  Text,
} from "@mantine/core";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useServerSearch } from "@/apis/hooks";
import { useDebouncedValue } from "@/utilities";

type SearchResultItem = {
  value: string;
  label: string;
  link: string;
  poster: string;
  type: string;
};

function useSearch(query: string) {
  const debouncedQuery = useDebouncedValue(query, 500);
  const { data } = useServerSearch(debouncedQuery, debouncedQuery.length >= 0);

  return useMemo<SearchResultItem[]>(
    () =>
      data?.map((v) => {
        const { link, label, poster, type, value } = (() => {
          if (v.sonarrSeriesId) {
            return {
              poster: v.poster,
              link: `/series/${v.sonarrSeriesId}`,
              type: "show",
              label: `${v.title} (${v.year})`,
              value: `s-${v.sonarrSeriesId}`,
            };
          }

          if (v.radarrId) {
            return {
              poster: v.poster,
              link: `/movies/${v.radarrId}`,
              type: "movie",
              value: `m-${v.radarrId}`,
              label: `${v.title} (${v.year})`,
            };
          }

          throw new Error("Unknown search result");
        })();

        return {
          value: value,
          poster: poster,
          label: label,
          type: type,
          link: link,
        };
      }) ?? [],
    [data],
  );
}

const optionsFilter: OptionsFilter = ({ options, search }) => {
  const lowercaseSearch = search.toLowerCase();
  const trimmedSearch = search.trim();

  return (options as ComboboxItem[]).filter((option) => {
    return (
      option.label.toLowerCase().includes(lowercaseSearch) ||
      option.label
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
    <Select
      placeholder="Search"
      withCheckIcon={false}
      leftSection={<FontAwesomeIcon icon={faSearch} />}
      rightSection={<></>}
      size="sm"
      searchable
      scrollAreaProps={{ type: "auto" }}
      maxDropdownHeight={400}
      data={results}
      value={query}
      onSearchChange={(a) => {
        setQuery(a);
      }}
      onBlur={() => setQuery("")}
      filter={optionsFilter}
      onOptionSubmit={(option) => {
        navigate(results.find((a) => a.value === option)?.link || "/");
      }}
      renderOption={(input) => {
        const result = results.find((r) => r.value === input.option.value);

        return (
          <>
            <Image src={result?.poster} w={35} h={50} />
            <Text p="xs">{result?.label}</Text>
          </>
        );
      }}
    />
  );
};

export default Search;
