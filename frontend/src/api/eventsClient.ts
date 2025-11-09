/**
 * WebSocket Event Client
 *
 * Subscribes to real-time CDC events from backend WebSocket server.
 * Handles connection lifecycle and event distribution to subscribers.
 */

import { ref } from "vue";

export interface CDCEvent {
  type: string;
  event_type: string;
  entity_id: string;
  entity_type: string;
  timestamp: string;
  data?: Record<string, unknown>;
  percentage?: number;
  message?: string;
}

export interface EventFilter {
  event_types?: string[];
  entity_types?: string[];
}

class EventsClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private subscriptions: Map<string, Set<(event: CDCEvent) => void>> = new Map();
  private isConnecting = false;
  private messageQueue: string[] = [];

  connectionStatus = ref<"connected" | "disconnected" | "connecting">(
    "disconnected"
  );
  eventCount = ref(0);
  lastEvent = ref<CDCEvent | null>(null);

  constructor(baseUrl?: string) {
    // Auto-detect backend URL
    if (typeof window !== "undefined") {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.hostname;
      const port = window.location.port;

      // If on localhost (dev), connect to localhost:8000 backend
      if (host === "localhost" && port && port !== "8000") {
        this.url = `${protocol}//localhost:8000/ws/events`;
      } else {
        // Otherwise use current origin with /ws path
        this.url = `${protocol}//${host}${port ? `:${port}` : ""}/ws/events`;
      }
    } else {
      this.url = baseUrl || "ws://localhost:8000/ws/events";
    }
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting) return;
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.isConnecting = true;
      this.connectionStatus.value = "connecting";

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log("WebSocket connected", this.url);
          this.connectionStatus.value = "connected";
          this.reconnectAttempts = 0;
          this.isConnecting = false;

          // Send any queued messages
          this.flushMessageQueue();

          // Start heartbeat
          this.startHeartbeat();

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as CDCEvent;
            this.handleEvent(data);
          } catch (e) {
            console.error("Failed to parse WebSocket message", e);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error", error);
          this.connectionStatus.value = "disconnected";
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = () => {
          console.log("WebSocket closed");
          this.connectionStatus.value = "disconnected";
          this.isConnecting = false;
          this.attemptReconnect();
        };
      } catch (e) {
        this.isConnecting = false;
        reject(e);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionStatus.value = "disconnected";
  }

  /**
   * Subscribe to specific event types
   * @param eventType Event type to subscribe to (e.g., "node_added", "*" for all)
   * @param callback Function to call when event received
   */
  subscribe(
    eventType: string,
    callback: (event: CDCEvent) => void
  ): () => void {
    if (!this.subscriptions.has(eventType)) {
      this.subscriptions.set(eventType, new Set());
    }
    this.subscriptions.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      const subs = this.subscriptions.get(eventType);
      if (subs) {
        subs.delete(callback);
      }
    };
  }

  /**
   * Set event filter on server
   * @param filter Event filter criteria
   */
  setFilter(filter: EventFilter): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("WebSocket not connected, queuing filter message");
      this.messageQueue.push(JSON.stringify({ action: "filter", ...filter }));
      return;
    }

    this.ws.send(JSON.stringify({ action: "filter", ...filter }));
  }

  /**
   * Get computed stats
   */
  get isConnected(): boolean {
    return this.connectionStatus.value === "connected";
  }

  /**
   * Test connection with ping
   */
  ping(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send("ping");
    }
  }

  private handleEvent(event: CDCEvent): void {
    this.eventCount.value++;
    this.lastEvent.value = event;

    // Broadcast to subscribers
    if (this.subscriptions.has("*")) {
      this.subscriptions.get("*")!.forEach((cb) => cb(event));
    }

    if (event.event_type && this.subscriptions.has(event.event_type)) {
      this.subscriptions.get(event.event_type)!.forEach((cb) => cb(event));
    }
  }

  private startHeartbeat(): void {
    const interval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ping();
      } else {
        clearInterval(interval);
      }
    }, 30000); // Ping every 30 seconds
  }

  private flushMessageQueue(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws.send(message);
      }
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((e) => console.error("Reconnect failed", e));
    }, delay);
  }
}

// Singleton instance
let clientInstance: EventsClient | null = null;

export function getEventsClient(): EventsClient {
  if (!clientInstance) {
    clientInstance = new EventsClient();
  }
  return clientInstance;
}

export default EventsClient;
