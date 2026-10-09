import { createContext, useContext } from "react";

const LoadingContext = createContext<boolean>(false);

export const useIsLoading = () => {
  const context = useContext(LoadingContext);

  return context;
};

export default LoadingContext.Provider;
