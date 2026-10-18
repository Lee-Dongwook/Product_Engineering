import { z } from "zod";

export const OrderActionEnum = z.enum(["APPROVED", "MODIFIED", "REJECTED"]);

export const OrderDecisionEventSchema = z.object({
  event_name: z.literal("order_decision_submitted"),
  user_id: z.string(),
  product_id: z.number(),
  purchase_order_id: z.number(),
  suggested_qty: z.number(),
  final_qty: z.number(),
  action: OrderActionEnum,
  rejection_reason: z.string().optional(),
  decision_time_ms: z.number(),
  timestamp: z.string().datetime(),
});

export type OrderDecisionEvent = z.infer<typeof OrderDecisionEventSchema>;
