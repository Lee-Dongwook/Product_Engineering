"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { trackOrderDecision } from "@/schemas/tracking";

interface OrderProposal {
  product_id: number;
  product_name: string;
  suggested_qty: number;
  current_stock: number;
  reasoning_summary: string;
}

export default function OrderApprovalPage() {
  const [loading, setLoading] = useState(false);

  const handleDecision = async (
    action: "APPROVED" | "REJECTED" | "MODIFIED",
    finalQty: number,
  ) => {
    const startTime = Date.now();

    await trackOrderDecision({
      event_name: "order_decision_submitted",
      user_id: "user_001",
      product_id: 101,
      purchase_order_id: 50,
      suggested_qty: 20,
      final_qty: finalQty,
      action: action,
      decision_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    });

    alert(`발주 제안이 ${action} 처리되었습니다.`);
  };

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-2xl font-bold mb-6">AI 공급망 발주 제안 검토</h1>
      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>상품 SKU-001 (무선 키보드)</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-2">
              AI 근거 요약: 예상 수요(40개) 및 안전재고 확보를 위해 MOQ 20단위로
              산출됨.
            </p>
            <div className="flex gap-4 items-center">
              <span>
                제안 수량: <strong>20개</strong>
              </span>
              <Button onClick={() => handleDecision("APPROVED", 20)}>
                승인
              </Button>
              <Button
                variant="outline"
                onClick={() => handleDecision("MODIFIED", 25)}
              >
                수량 수정 (25개)
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleDecision("REJECTED", 0)}
              >
                거절
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
