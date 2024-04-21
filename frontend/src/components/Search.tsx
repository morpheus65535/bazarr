import { useServerSearch } from "@/apis/hooks";
import { useDebouncedValue } from "@/utilities";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Anchor,
  Autocomplete,
  ComboboxItem,
  OptionsFilter,
} from "@mantine/core";
import { FunctionComponent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import styles from "./Search.module.scss";

type SearchResultItem = {
  value: string;
  link: string;
};

function useSearch(query: string) {
  const debouncedQuery = useDebouncedValue(query, 500);
  const { data } = useServerSearch(debouncedQuery, debouncedQuery.length > 0);

  return useMemo<SearchResultItem[]>(
    () =>
      data?.map((v) => {
        let link: string;
        if (v.sonarrSeriesId) {
          link = `/series/${v.sonarrSeriesId}`;
        } else if (v.radarrId) {
          link = `/movies/${v.radarrId}`;
        } else {
          throw new Error("Unknown search result");
        }

        return {
          value: `${v.title} (${v.year})`,
          link,
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
      option.value.toLowerCase().includes(lowercaseSearch) ||
      option.value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .includes(trimmedSearch)
    );
  });
};

const ResultComponent = ({ name, link }: { name: string; link: string }) => {
  return (
    <Anchor
      component={Link}
      to={link}
      underline="never"
      className={styles.result}
      p="sm"
    >
      {name}
    </Anchor>
  );
};

const Search: FunctionComponent = () => {
  const [query, setQuery] = useState("");

  const results = useSearch(query);

  return (
    <Autocomplete
      leftSection={<FontAwesomeIcon icon={faSearch} />}
      renderOption={(input) => (
        <ResultComponent
          name={input.option.value}
          link={
            results.find((a) => a.value === input.option.value)?.link || "/"
          }
        />
      )}
      placeholder="Search"
      size="sm"
      data={results}
      value={query}
      onChange={setQuery}
      onBlur={() => setQuery("")}
      filter={optionsFilter}
    ></Autocomplete>
  );
};

export default Search;
