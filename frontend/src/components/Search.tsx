import { FunctionComponent, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import {
  ComboboxItem,
  em,
  Flex,
  Image,
  OptionsFilter,
  Select,
  Text,
} from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
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

  const isMobile = useMediaQuery(`(max-width: ${em(750)})`);

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
          <Flex>
            <Image src={result?.poster} w={55} h={70} />
            <Text size={isMobile ? "xs" : "md"} pl="xs" pr="xs" lineClamp={3}>
              {result?.label}
            </Text>
          </Flex>
        );
      }}
    />
  );
};

export default Search;
