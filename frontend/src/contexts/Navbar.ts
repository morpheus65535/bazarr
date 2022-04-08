import { createContext, useContext } from "react";

const NavbarContext = createContext<{
  showed: boolean;
  show: (showed: boolean) => void;
} | null>(null);

export function useNavbar() {
  const context = useContext(NavbarContext);

  if (context === null) {
    throw new Error("NavbarShowedContext not initialized");
  }

  return context;
}

export default NavbarContext.Provider;
