import { QueryClient } from "react-query";

const queryClient = new QueryClient();

queryClient.setDefaultOptions({
  queries: {
    staleTime: 1000 * 60,
  },
});

export default queryClient;
