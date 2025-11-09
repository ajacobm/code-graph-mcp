/**
 * Vue Composable for WebSocket Event Subscriptions
 *
 * Usage:
 *   const { isConnected, subscribe, eventCount } = useEvents()
 *   subscribe('node_added', (event) => {
 *     console.log('Node added:', event.data)
 *   })
 */

import { onMounted, onUnmounted } from "vue";
import { getEventsClient, type CDCEvent, type EventFilter } from "../api/eventsClient";

export function useEvents() {
  const client = getEventsClient();

  onMounted(async () => {
    try {
      await client.connect();
    } catch (e) {
      console.error("Failed to connect to events", e);
    }
  });

  onUnmounted(() => {
    client.disconnect();
  });

  return {
    isConnected: client.connectionStatus,
    eventCount: client.eventCount,
    lastEvent: client.lastEvent,
    subscribe: (eventType: string, callback: (event: CDCEvent) => void) =>
      client.subscribe(eventType, callback),
    setFilter: (filter: EventFilter) => client.setFilter(filter),
    ping: () => client.ping(),
    disconnect: () => client.disconnect(),
  };
}

export default useEvents;
