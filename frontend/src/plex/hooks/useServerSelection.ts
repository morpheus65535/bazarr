import { useCallback, useReducer } from "react";
import type { PlexServer } from "@/plex/queries/plex";

interface ServerSelectionState {
  selectedServerId: string;
  isSelecting: boolean;
  isSaved: boolean;
  selectedServer: PlexServer | null;
}

type ServerSelectionAction =
  | { type: "SET_SELECTED_SERVER_ID"; payload: string }
  | { type: "SET_SELECTING"; payload: boolean }
  | { type: "SET_SAVED"; payload: boolean }
  | { type: "SET_SELECTED_SERVER"; payload: PlexServer | null }
  | { type: "RESET" };

const initialState: ServerSelectionState = {
  selectedServerId: "",
  isSelecting: false,
  isSaved: false,
  selectedServer: null,
};

function serverSelectionReducer(
  state: ServerSelectionState,
  action: ServerSelectionAction,
): ServerSelectionState {
  switch (action.type) {
    case "SET_SELECTED_SERVER_ID":
      return { ...state, selectedServerId: action.payload };
    case "SET_SELECTING":
      return { ...state, isSelecting: action.payload };
    case "SET_SAVED":
      return { ...state, isSaved: action.payload };
    case "SET_SELECTED_SERVER":
      return {
        ...state,
        selectedServer: action.payload,
        selectedServerId: action.payload?.machineIdentifier || "",
      };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

/**
 * Server Selection Hook - React Query Version
 *
 * Manages server selection state using a reducer pattern for better consistency.
 * This hook is designed to work with React Query-based server management.
 */
export const useServerSelection = () => {
  const [state, dispatch] = useReducer(serverSelectionReducer, initialState);

  const setSelectedServerId = useCallback((serverId: string) => {
    dispatch({ type: "SET_SELECTED_SERVER_ID", payload: serverId });
  }, []);

  const setSelecting = useCallback((selecting: boolean) => {
    dispatch({ type: "SET_SELECTING", payload: selecting });
  }, []);

  const setSaved = useCallback((saved: boolean) => {
    dispatch({ type: "SET_SAVED", payload: saved });
  }, []);

  const setSelectedServer = useCallback((server: PlexServer | null) => {
    dispatch({ type: "SET_SELECTED_SERVER", payload: server });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return {
    selectedServerId: state.selectedServerId,
    isSelecting: state.isSelecting,
    isSaved: state.isSaved,
    selectedServer: state.selectedServer,
    setSelectedServerId,
    setSelecting,
    setSaved,
    setSelectedServer,
    reset,
  };
};
