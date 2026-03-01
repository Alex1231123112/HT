import { createContext, PropsWithChildren, useContext, useEffect } from "react";

import { useAdminData } from "../hooks/useAdminData";

type AdminState = ReturnType<typeof useAdminData>;

const AdminContext = createContext<AdminState | null>(null);

export function AdminProvider({ children }: PropsWithChildren) {
  const state = useAdminData();
  const { tokenReady, refresh, setError } = state;

  useEffect(() => {
    if (tokenReady) {
      void refresh().catch((error: unknown) => setError(String(error)));
    }
  }, [tokenReady, refresh, setError]);

  return <AdminContext.Provider value={state}>{children}</AdminContext.Provider>;
}

export function useAdmin() {
  const context = useContext(AdminContext);
  if (!context) {
    throw new Error("useAdmin must be used within AdminProvider");
  }
  return context;
}
