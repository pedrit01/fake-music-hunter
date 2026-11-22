import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

/** Estado del servidor. Se consulta periódicamente para detectar caídas. */
export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 10_000,
    retry: false,
  });
}
