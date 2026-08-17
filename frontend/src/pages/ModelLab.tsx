import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import {
  FlaskConical,
  CheckCircle2,
  CircleDashed,
  BrainCircuit,
  Activity,
  ShieldCheck,
} from "lucide-react"
import { api } from "@/lib/api"
import type { ModelVersionItem, ModelDetailItem } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { EmptyState } from "@/components/ui/empty-state"
import { formatDateTime } from "@/lib/utils"

function MetricCell({ label, value, highlight }: { label: string; value: number | null; highlight?: boolean }) {
  const color = highlight ? "#10b981" : undefined
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 px-3 py-2 text-center">
      <p className="text-xs text-[var(--muted-foreground)]">{label}</p>
      <p className="text-lg font-bold" style={{ color }}>
        {value === null || value === undefined ? "—" : (value * 100).toFixed(1)}
        <span className="text-xs font-normal text-[var(--muted-foreground)]">%</span>
      </p>
    </div>
  )
}

function ConfusionMatrix({ matrix }: { matrix: number[][] | undefined }) {
  if (!matrix || matrix.length !== 2) return null
  return (
    <div className="inline-block overflow-hidden rounded-lg border border-[var(--border)]">
      <div className="grid grid-cols-3 text-xs">
        <div className="px-3 py-1.5 bg-[var(--muted)] font-medium text-[var(--muted-foreground)]"></div>
        <div className="px-3 py-1.5 bg-[var(--muted)] text-center font-medium">Pred: Safe</div>
        <div className="px-3 py-1.5 bg-[var(--muted)] text-center font-medium">Pred: At Risk</div>
        <div className="px-3 py-1.5 bg-[var(--muted)] font-medium text-[var(--muted-foreground)]">Actual: Safe</div>
        <div className="px-3 py-1.5 text-center font-bold text-emerald-600">{matrix[0][0]}</div>
        <div className="px-3 py-1.5 text-center font-bold text-red-500">{matrix[0][1]}</div>
        <div className="px-3 py-1.5 bg-[var(--muted)] font-medium text-[var(--muted-foreground)]">Actual: At Risk</div>
        <div className="px-3 py-1.5 text-center font-bold text-red-500">{matrix[1][0]}</div>
        <div className="px-3 py-1.5 text-center font-bold text-emerald-600">{matrix[1][1]}</div>
      </div>
    </div>
  )
}

function ModelCard({ model, onActivate, activating }: { model: ModelVersionItem; onActivate: (id: string) => void; activating: boolean }) {
  const { data: detail } = useQuery({
    queryKey: ["model-detail", model.model_id],
    queryFn: () => api.get<ModelDetailItem>(`/models/${model.model_id}`),
  })

  const maxImportance = Math.max(...(detail?.feature_importance?.map((f) => f.importance) ?? [0.01]), 0.01)

  return (
    <Card className={model.is_active ? "ring-2 ring-[var(--primary)]/60" : ""}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-[var(--primary)]" />
            {model.algorithm}
          </CardTitle>
          {model.is_active ? (
            <Badge variant="success">
              <CheckCircle2 className="h-3 w-3" /> Production
            </Badge>
          ) : (
            <Badge variant="secondary">Inactive</Badge>
          )}
        </div>
        <CardDescription>
          Trained {formatDateTime(model.training_date)} · {model.training_rows} training rows
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          <MetricCell label="Accuracy" value={model.accuracy} highlight={model.is_active} />
          <MetricCell label="Precision" value={model.precision} />
          <MetricCell label="Recall" value={model.recall} />
          <MetricCell label="F1" value={model.f1_score} />
          <MetricCell label="ROC-AUC" value={model.roc_auc} />
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div>
            <p className="mb-1.5 text-xs font-medium text-[var(--muted-foreground)]">Confusion Matrix</p>
            <ConfusionMatrix matrix={detail?.confusion_matrix?.matrix} />
          </div>
          <div className="min-w-52 flex-1">
            <p className="mb-1.5 text-xs font-medium text-[var(--muted-foreground)]">Feature Importance</p>
            <div className="space-y-1.5">
              {(detail?.feature_importance ?? []).map((f) => (
                <div key={f.feature} className="flex items-center gap-2 text-xs">
                  <span className="w-32 truncate capitalize text-[var(--muted-foreground)]">
                    {f.feature.replace(/_/g, " ")}
                  </span>
                  <Progress
                    value={(f.importance / maxImportance) * 100}
                    className="h-1.5"
                    indicatorClassName={f.importance === maxImportance ? "bg-[#6366f1]" : undefined}
                  />
                  <span className="w-12 text-right font-medium">{f.importance.toFixed(3)}</span>
                </div>
              ))}
              {!detail?.feature_importance?.length && (
                <p className="text-xs text-[var(--muted-foreground)]">No importance data.</p>
              )}
            </div>
          </div>
        </div>

        {!model.is_active && (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => onActivate(model.model_id)}
            disabled={activating}
          >
            <ShieldCheck className="h-4 w-4" /> Set as production model
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

export default function ModelLab() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["models"],
    queryFn: () => api.get<ModelVersionItem[]>("/models"),
  })

  const activate = useMutation({
    mutationFn: (modelId: string) => api.post(`/models/${modelId}/activate`),
    onSuccess: () => {
      toast.success("Production model updated")
      queryClient.invalidateQueries({ queryKey: ["models"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Activation failed"),
  })

  const active = data?.find((m) => m.is_active)

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Model Lab</h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          Compare trained models, inspect metrics, and select the production model.
        </p>
      </div>

      {/* Current production model */}
      <Card className="border-indigo-500/30 bg-indigo-500/5">
        <CardContent className="flex flex-wrap items-center gap-4 p-5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--primary)]/10 text-[var(--primary)]">
            <BrainCircuit className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold">Current Production Model</p>
            {active ? (
              <p className="text-sm text-[var(--muted-foreground)]">
                {active.algorithm} · F1 {active.f1_score !== null ? (active.f1_score * 100).toFixed(1) : "—"}% · Accuracy{" "}
                {active.accuracy !== null ? (active.accuracy * 100).toFixed(1) : "—"}% · Trained{" "}
                {formatDateTime(active.training_date)}
              </p>
            ) : (
              <p className="text-sm text-[var(--muted-foreground)]">
                No model trained yet — upload a dataset and train from the Dataset page.
              </p>
            )}
          </div>
          <Badge variant="outline" className="text-xs">
            <Activity className="h-3 w-3" /> {data?.length ?? 0} version(s) stored
          </Badge>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      ) : !data?.length ? (
        <EmptyState
          icon={FlaskConical}
          title="No models trained yet"
          description="Train Random Forest and Logistic Regression models from the Dataset page."
          action={<Button onClick={() => (window.location.href = "/datasets")}>Go to Dataset</Button>}
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.map((m) => (
            <ModelCard key={m.model_id} model={m} onActivate={(id) => activate.mutate(id)} activating={activate.isPending} />
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Model selection rationale</CardTitle>
          <CardDescription>
            The best model is chosen using a weighted composite score: F1 × 0.5 + ROC-AUC × 0.3 + Accuracy × 0.2 —
            accuracy alone is never the sole criterion.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
            <CircleDashed className="h-4 w-4 text-[var(--primary)]" />
            Every training run is stored as an immutable version (model ID, algorithm, date, metrics, feature list,
            row count). Historical models are never silently replaced.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
