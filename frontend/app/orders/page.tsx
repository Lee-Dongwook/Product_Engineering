"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetcher } from "@/lib/api";
import { trackOrderDecision } from "@/utils/track";

interface Product {
  id: number;
  sku: string;
  name: string;
  current_stock: number;
}

interface OrderProposal {
  purchase_order_id: number;
  product_id: number;
  suggested_qty: number;
  reasoning_summary: string;
}

export default function OrderApprovalPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState("");
  const [proposal, setProposal] = useState<OrderProposal>();
  const [finalQty, setFinalQty] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetcher<Product[]>("/inventory/products")
      .then((items) => {
        setProducts(items);
        if (items[0]) setProductId(String(items[0].id));
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const selectedProduct = products.find((product) => product.id === Number(productId));

  const runPrediction = async () => {
    if (!productId) return;

    setSubmitting(true);
    setError("");
    try {
      const result = await fetcher<OrderProposal>(`/orders/run-prediction/${productId}`, {
        method: "POST",
      });
      setProposal(result);
      setFinalQty(result.suggested_qty);
    } catch (err) {
      setError(err instanceof Error ? err.message : "발주 예측에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDecision = async (action: "APPROVED" | "REJECTED" | "MODIFIED") => {
    if (!proposal) return;
    if (action !== "REJECTED" && (!Number.isInteger(finalQty) || finalQty < 0)) {
      setError("최종 수량은 0 이상의 정수여야 합니다.");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      await trackOrderDecision({
        event_name: "order_decision_submitted",
        user_id: "user_001",
        product_id: proposal.product_id,
        purchase_order_id: proposal.purchase_order_id,
        suggested_qty: proposal.suggested_qty,
        final_qty: action === "REJECTED" ? 0 : finalQty,
        action,
        decision_time_ms: 0,
        timestamp: new Date().toISOString(),
      });
      alert(`발주 제안이 ${action} 처리되었습니다.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "결정 저장에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto py-10">
      <h1 className="mb-6 text-2xl font-bold">AI 공급망 발주 제안 검토</h1>
      <Card>
        <CardHeader><CardTitle>발주 대상 상품</CardTitle></CardHeader>
        <CardContent className="grid gap-4">
          <select
            aria-label="발주 대상 상품"
            className="max-w-md rounded border border-gray-300 p-2"
            disabled={loading || submitting || products.length === 0}
            value={productId}
            onChange={(event) => {
              setProductId(event.target.value);
              setProposal(undefined);
            }}
          >
            {products.map((product) => (
              <option key={product.id} value={product.id}>{product.sku} · {product.name}</option>
            ))}
          </select>
          <Button className="w-fit" disabled={!productId || submitting} onClick={runPrediction}>
            {submitting ? "처리 중..." : "AI 발주 예측 실행"}
          </Button>
          {loading && <p className="text-sm text-gray-500">상품을 불러오는 중입니다.</p>}
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
        </CardContent>
      </Card>

      {proposal && selectedProduct && (
        <Card className="mt-4">
          <CardHeader><CardTitle>상품 {selectedProduct.sku} ({selectedProduct.name})</CardTitle></CardHeader>
          <CardContent>
            <p className="mb-2 text-sm text-gray-500">AI 근거 요약: {proposal.reasoning_summary}</p>
            <p className="mb-4 text-sm text-gray-500">현재 재고: {selectedProduct.current_stock}개</p>
            <div className="flex flex-wrap items-center gap-4">
              <span>제안 수량: <strong>{proposal.suggested_qty}개</strong></span>
              <label className="flex items-center gap-2">
                최종 수량
                <input
                  className="w-20 rounded border border-gray-300 p-2"
                  min="0"
                  type="number"
                  value={finalQty}
                  onChange={(event) => setFinalQty(Number(event.target.value))}
                />
              </label>
              <Button disabled={submitting} onClick={() => handleDecision("APPROVED")}>승인</Button>
              <Button disabled={submitting} variant="outline" onClick={() => handleDecision("MODIFIED")}>수량 수정</Button>
              <Button disabled={submitting} variant="destructive" onClick={() => handleDecision("REJECTED")}>거절</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
