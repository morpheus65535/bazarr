import { createContext, useContext } from "react";

const OnlineContext = createContext<{
  online: boolean;
  setOnline: (online: boolean) => void;
} | null>(null);

export const useIsOnline = () => {
  const context = useContext(OnlineContext);

  if (context === null) {
    throw new Error("useIsOnline must be used within a OnlineProvider");
  }

  return context.online;
};

export const useSetOnline = () => {
  const context = useContext(OnlineContext);

  if (context === null) {
    throw new Error("useSetOnline must be used within a OnlineProvider");
  }

  return context.setOnline;
};

export default OnlineContext.Provider;
