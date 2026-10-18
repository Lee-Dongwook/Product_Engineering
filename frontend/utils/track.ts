import {
  OrderDecisionEvent,
  OrderDecisionEventSchema,
} from "../schemas/tracking";

export async function trackOrderDecision(eventData: OrderDecisionEvent) {
  const parseResult = OrderDecisionEventSchema.safeParse(eventData);
  if (!parseResult.success) {
    console.error("Invalid tracking event schema:", parseResult.error);
    return;
  }

  const validData = parseResult.data;

  const blob = new Blob([JSON.stringify(validData)], {
    type: "application/json",
  });

  if (navigator.sendBeacon) {
    navigator.sendBeacon("/api/v1/tracking/events", blob);
  } else {
    await fetch("/api/v1/tracking/events", {
      method: "POST",
      body: JSON.stringify(validData),
      headers: { "Content-Type": "application/json" },
      keepalive: true,
    });
  }
}
