import { Loader } from "@mantine/core";
import { FunctionComponent } from "react";

export const LoadingIndicator: FunctionComponent = ({ children }) => {
  return (
    <div className="d-flex flex-column flex-grow-1 align-items-center py-5">
      <Loader></Loader>
      {children}
    </div>
  );
};

export * from "./buttons";
export * from "./header";
export * from "./inputs";
export * from "./LanguageSelector";
export * from "./SearchBar";
export * from "./tables";
