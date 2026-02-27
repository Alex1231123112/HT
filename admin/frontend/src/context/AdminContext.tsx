import { createContext, PropsWithChildren, useContext, useEffect } from "react";

import { useAdminData } from "../hooks/useAdminData";

type AdminState = ReturnType<typeof useAdminData>;

const AdminContext = createContext<AdminState | null>(null);

export function AdminProvider({ children }: PropsWithChildren) {
  const state = useAdminData();

  useEffect(() => {
    if (state.tokenReady) {
      void state.refresh().catch((error: unknown) => state.setError(String(error)));
    }
  }, [state.tokenReady]);

  return <AdminContext.Provider value={state}>{children}</AdminContext.Provider>;
}

export function useAdmin() {
  const context = useContext(AdminContext);
  if (!context) {
    throw new Error("useAdmin must be used within AdminProvider");
  }
  return context;
}
