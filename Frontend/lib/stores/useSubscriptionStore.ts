import { create } from "zustand";

interface SubscriptionStore {
  refetchFlag: boolean;
  triggerRefetch: () => void;
}

export const useSubscriptionStore = create<SubscriptionStore>((set) => ({
  refetchFlag: false,
  triggerRefetch: () => set((state) => ({ refetchFlag: !state.refetchFlag })),
}));
