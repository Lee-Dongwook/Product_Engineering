import {
  OrderDecisionEvent,
  OrderDecisionEventSchema,
} from "../schemas/tracking";
import { fetcher } from "../lib/api";

export async function trackOrderDecision(eventData: OrderDecisionEvent) {
  const parseResult = OrderDecisionEventSchema.safeParse(eventData);
  if (!parseResult.success) {
    console.error("Invalid tracking event schema:", parseResult.error);
    return;
  }

  await fetcher("/tracking/events", {
    method: "POST",
    body: JSON.stringify(parseResult.data),
  });
}
