import { Autocomplete } from "@mantine/core";
import { FunctionComponent } from "react";

// function useSearch(query: string) {
//   const { data } = useServerSearch(query, query.length > 0);

//   return useMemo(
//     () =>
//       data?.map((v) => {
//         let link: string;
//         let id: string;
//         if (v.sonarrSeriesId) {
//           link = `/series/${v.sonarrSeriesId}`;
//           id = `series-${v.sonarrSeriesId}`;
//         } else if (v.radarrId) {
//           link = `/movies/${v.radarrId}`;
//           id = `movie-${v.radarrId}`;
//         } else {
//           link = "";
//           id = uniqueId("unknown");
//         }

//         return {
//           name: `${v.title} (${v.year})`,
//           link,
//           id,
//         };
//       }) ?? [],
//     [data]
//   );
// }
export interface SearchResult {
  id: string;
  name: string;
  link?: string;
}

interface Props {
  className?: string;
  onFocus?: () => void;
  onBlur?: () => void;
}

export const SearchBar: FunctionComponent<Props> = ({
  onFocus,
  onBlur,
  className,
}) => {
  // const [display, setDisplay] = useState("");
  // const [query, setQuery] = useState("");

  // const [debounce] = useThrottle(setQuery, 500);
  // useEffect(() => {
  //   debounce(display);
  // }, [debounce, display]);

  // const results = useSearch(query);

  // const navigate = useNavigate();

  // const clear = useCallback(() => {
  //   setDisplay("");
  //   setQuery("");
  // }, []);

  // const items = useMemo(() => {
  //   const its = results.map((v) => (
  //     <Dropdown.Item
  //       key={v.id}
  //       eventKey={v.link}
  //       disabled={v.link === undefined}
  //     >
  //       <span>{v.name}</span>
  //     </Dropdown.Item>
  //   ));

  //   if (its.length === 0) {
  //     its.push(<Dropdown.Header key="notify">No Found</Dropdown.Header>);
  //   }

  //   return its;
  // }, [results]);

  return <Autocomplete data={[]}></Autocomplete>;
  // return (
  //   <Dropdown
  //     show={query.length !== 0}
  //     className={className}
  //     onFocus={onFocus}
  //     onBlur={onBlur}
  //     onSelect={(link) => {
  //       if (link) {
  //         clear();
  //         navigate(link);
  //       }
  //     }}
  //   >
  //     <Form.Control
  //       type="text"
  //       size="sm"
  //       placeholder="Search..."
  //       value={display}
  //       onChange={(e) => setDisplay(e.currentTarget.value)}
  //     ></Form.Control>
  //     <Dropdown.Menu style={{ maxHeight: 256, overflowY: "auto" }}>
  //       {items}
  //     </Dropdown.Menu>
  //   </Dropdown>
  // );
};
