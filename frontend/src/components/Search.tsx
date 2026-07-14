import { FunctionComponent } from "react";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { spotlightApi } from "@/components/AppSpotlight";
import Action from "@/components/inputs/Action";

const Search: FunctionComponent = () => {
  return (
    <Action
      hiddenFrom="sm"
      label="Search"
      icon={faSearch}
      size="sm"
      onClick={() => spotlightApi.open()}
    />
  );
};

export default Search;
