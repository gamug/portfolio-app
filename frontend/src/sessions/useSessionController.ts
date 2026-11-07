import { useSyncExternalStore } from "react";
import type { SessionController, SessionState } from "./SessionController";

export function useSessionController(controller: SessionController): SessionState {
  return useSyncExternalStore(controller.subscribe, controller.getSnapshot, controller.getSnapshot);
}
