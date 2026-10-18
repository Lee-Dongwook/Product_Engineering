"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetcher } from "@/lib/api";

interface Product {
  id: number;
  sku: string;
  name: string;
  current_stock: number;
}

type WorkflowStepId =
  | "demand_agent"
  | "supplier_agent"
  | "supervisor"
  | "operator_decision";

type WorkflowStatus = "pending" | "completed" | "error";

interface WorkflowStep {
  id: WorkflowStepId;
  status: WorkflowStatus;
  message: string;
  input_summary?: string;
  output_summary?: string;
}

interface OrderProposal {
  purchase_order_id: number;
  product_id: number;
  suggested_qty: number;
  reasoning_summary: string;
  execution_logs?: string[];
  workflow_steps: WorkflowStep[];
}

const WORKFLOW_LABELS: Record<WorkflowStepId, string> = {
  demand_agent: "수요 예측",
  supplier_agent: "공급 조건 검토",
  supervisor: "최종 발주 제안",
  operator_decision: "운영자 결정",
};

const AI_STEP_IDS: WorkflowStepId[] = [
  "demand_agent",
  "supplier_agent",
  "supervisor",
];

const INITIAL_WORKFLOW: WorkflowStep[] = [
  {
    id: "demand_agent",
    status: "pending",
    message: "발주 예측 실행을 기다리고 있습니다.",
  },
  {
    id: "supplier_agent",
    status: "pending",
    message: "수요 예측 이후 공급 조건을 검토합니다.",
  },
  {
    id: "supervisor",
    status: "pending",
    message: "앞 단계의 결과를 바탕으로 최종 수량을 산출합니다.",
  },
  {
    id: "operator_decision",
    status: "pending",
    message: "AI 제안 생성 후 운영자가 결정할 수 있습니다.",
  },
];

function statusLabel(status: WorkflowStatus) {
  switch (status) {
    case "completed":
      return "완료";
    case "error":
      return "오류";
    default:
      return "대기";
  }
}

function statusClass(status: WorkflowStatus) {
  switch (status) {
    case "completed":
      return "border-emerald-300 bg-emerald-50 text-emerald-800";
    case "error":
      return "border-red-300 bg-red-50 text-red-800";
    default:
      return "border-gray-200 bg-gray-50 text-gray-600";
  }
}

export default function OrderApprovalPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState("");
  const [proposal, setProposal] = useState<OrderProposal>();
  const [workflowSteps, setWorkflowSteps] =
    useState<WorkflowStep[]>(INITIAL_WORKFLOW);
  const [selectedStepId, setSelectedStepId] =
    useState<WorkflowStepId>("demand_agent");

  const [finalQty, setFinalQty] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [decisionMessage, setDecisionMessage] = useState("");

  useEffect(() => {
    fetcher<Product[]>("/inventory/products")
      .then((items) => {
        setProducts(items);
        if (items[0]) setProductId(String(items[0].id));
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const selectedProduct = products.find(
    (product) => product.id === Number(productId),
  );

  const selectedStep = workflowSteps.find((step) => step.id === selectedStepId);

  const decisionStep = workflowSteps.find(
    (step) => step.id === "operator_decision",
  );

  const resetWorkflow = () => {
    setProposal(undefined);
    setWorkflowSteps(INITIAL_WORKFLOW);
    setSelectedStepId("demand_agent");
    setDecisionMessage("");
    setError("");
  };

  const runPrediction = async () => {
    if (!productId) return;

    setSubmitting(true);
    setError("");
    setDecisionMessage("");
    setProposal(undefined);
    setSelectedStepId("demand_agent");

    setWorkflowSteps(
      INITIAL_WORKFLOW.map((step) => ({
        ...step,
        message:
          step.id === "demand_agent"
            ? "발주 예측 API 응답을 기다리고 있습니다."
            : step.message,
      })),
    );

    try {
      const result = await fetcher<OrderProposal>(
        `/orders/run-prediction/${productId}`,
        {
          method: "POST",
        },
      );
      setProposal(result);
      setFinalQty(result.suggested_qty);

      setWorkflowSteps([
        ...result.workflow_steps,
        {
          id: "operator_decision",
          status: "pending",
          message:
            "제안 수량을 검토한 후 승인, 수량 수정 또는 거절을 선택하세요.",
          input_summary: `AI 제안 수량 ${result.suggested_qty}개`,
          output_summary: "운영자 결정 대기",
        },
      ]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "발주 예측에 실패했습니다.";

      setError(message);

      setWorkflowSteps((steps) =>
        steps.map((step) => {
          if (AI_STEP_IDS.includes(step.id)) {
            return {
              ...step,
              status: "error",
              message,
            };
          }

          return {
            ...step,
            status: "pending",
            message: "발주 예측 실패로 운영자 결정을 진행할 수 없습니다.",
          };
        }),
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleDecision = async (
    action: "APPROVED" | "REJECTED" | "MODIFIED",
  ) => {
    if (!proposal) return;
    if (
      action !== "REJECTED" &&
      (!Number.isInteger(finalQty) || finalQty < 0)
    ) {
      setError("최종 수량은 0 이상의 정수여야 합니다.");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      await fetcher(`/orders/${proposal.purchase_order_id}/decision`, {
        method: "PATCH",
        body: JSON.stringify({
          action,
          final_qty: action === "REJECTED" ? 0 : finalQty,
        }),
      });

      const decisionLabel =
        action === "APPROVED"
          ? "승인"
          : action === "MODIFIED"
            ? "수정"
            : "거절";

      setDecisionMessage(`발주 제안이 ${decisionLabel} 처리되었습니다.`);

      setWorkflowSteps((steps) =>
        steps.map((step) => {
          if (step.id !== "operator_decision") {
            return step;
          }

          return {
            ...step,
            status: "completed",
            message: `운영자가 발주 제안을 ${decisionLabel}했습니다.`,
            output_summary:
              action === "REJECTED"
                ? "발주 거절"
                : `최종 발주 수량 ${finalQty}개`,
          };
        }),
      );
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "결정 저장에 실패했습니다.";

      setError(message);

      setWorkflowSteps((steps) =>
        steps.map((step) =>
          step.id === "operator_decision"
            ? {
                ...step,
                status: "error",
                message,
              }
            : step,
        ),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto py-10">
      <h1 className="mb-6 text-2xl font-bold">AI 공급망 발주 제안 검토</h1>
      <Card>
        <CardHeader>
          <CardTitle>발주 대상 상품</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <select
            aria-label="발주 대상 상품"
            className="max-w-md rounded border border-gray-300 p-2"
            disabled={loading || submitting || products.length === 0}
            value={productId}
            onChange={(event) => {
              setProductId(event.target.value);
              resetWorkflow();
            }}
          >
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.sku} · {product.name}
              </option>
            ))}
          </select>
          <Button
            className="w-fit"
            disabled={!productId || submitting}
            onClick={runPrediction}
          >
            {submitting ? "처리 중..." : "AI 발주 예측 실행"}
          </Button>
          {loading && (
            <p className="text-sm text-gray-500">상품을 불러오는 중입니다.</p>
          )}
          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}
          {decisionMessage && (
            <p className="text-sm text-green-700" role="status">
              {decisionMessage}
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>AI 발주 워크플로우</CardTitle>
        </CardHeader>

        <CardContent>
          <ol className="grid gap-3 md:grid-cols-4">
            {workflowSteps.map((step, index) => (
              <li key={step.id}>
                <button
                  type="button"
                  aria-pressed={selectedStepId === step.id}
                  onClick={() => setSelectedStepId(step.id)}
                  className={`h-full w-full rounded-lg border p-4 text-left transition ${
                    selectedStepId === step.id
                      ? "border-blue-500 ring-2 ring-blue-100"
                      : "border-gray-200"
                  }`}
                >
                  <span className="mb-2 block text-xs text-gray-500">
                    STEP {index + 1}
                  </span>

                  <span className="block font-semibold">
                    {WORKFLOW_LABELS[step.id]}
                  </span>

                  <span
                    className={`mt-3 inline-flex rounded-full border px-2 py-1 text-xs ${statusClass(step.status)}`}
                  >
                    {statusLabel(step.status)}
                  </span>
                </button>
              </li>
            ))}
          </ol>

          {selectedStep && (
            <section
              className="mt-4 rounded-lg border border-gray-200 p-4"
              aria-live="polite"
            >
              <h3 className="font-semibold">
                {WORKFLOW_LABELS[selectedStep.id]} 상세
              </h3>

              <p className="mt-2 text-sm text-gray-700">
                {selectedStep.message}
              </p>

              <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-medium uppercase text-gray-500">
                    입력 요약
                  </dt>
                  <dd className="mt-1 text-sm">
                    {selectedStep.input_summary ??
                      "아직 제공된 입력 정보가 없습니다."}
                  </dd>
                </div>

                <div>
                  <dt className="text-xs font-medium uppercase text-gray-500">
                    출력 요약
                  </dt>
                  <dd className="mt-1 text-sm">
                    {selectedStep.output_summary ??
                      "단계 실행 후 결과가 표시됩니다."}
                  </dd>
                </div>
              </dl>
            </section>
          )}
        </CardContent>
      </Card>

      {proposal && selectedProduct && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>
              상품 {selectedProduct.sku} ({selectedProduct.name})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-2 text-sm text-gray-500">
              AI 근거 요약: {proposal.reasoning_summary}
            </p>
            <p className="mb-4 text-sm text-gray-500">
              현재 재고: {selectedProduct.current_stock}개
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <span>
                제안 수량: <strong>{proposal.suggested_qty}개</strong>
              </span>
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
              <Button
                disabled={submitting || decisionStep?.status === "completed"}
                onClick={() => handleDecision("APPROVED")}
              >
                승인
              </Button>
              <Button
                disabled={submitting || decisionStep?.status === "completed"}
                variant="outline"
                onClick={() => handleDecision("MODIFIED")}
              >
                수량 수정
              </Button>
              <Button
                disabled={submitting || decisionStep?.status === "completed"}
                variant="destructive"
                onClick={() => handleDecision("REJECTED")}
              >
                거절
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
