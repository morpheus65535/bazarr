import { QueryClient } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
      staleTime: 1000 * 60,
      networkMode: "offlineFirst",
      placeholderData: (previousData: object) => previousData,
    },
    mutations: {
      networkMode: "offlineFirst",
    },
  },
});

export default queryClient;
