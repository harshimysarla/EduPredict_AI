import { useState, useRef } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import {
  Upload,
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FlaskConical,
  Table2,
  FileWarning,
  Loader2,
  FileSpreadsheet,
} from "lucide-react"
import { api } from "@/lib/api"
import type { DatasetItem, DatasetPreview, ImportValidationReport, ImportResult, ImportHistoryItem } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { formatDateTime } from "@/lib/utils"

const REQUIRED_COLUMNS = [
  "student_id",
  "attendance",
  "previous_performance",
  "internal_marks",
  "assignment_score",
  "engagement",
  "study_hours",
  "target",
]

export default function Dataset() {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const { data: datasets, isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.get<DatasetItem[]>("/datasets"),
  })

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ["dataset-preview", selected],
    queryFn: () => api.get<DatasetPreview>(`/datasets/${selected}/validate`),
    enabled: selected !== null,
  })

  const upload = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData()
      fd.append("file", file)
      fd.append("name", file.name.replace(".csv", ""))
      return api.upload<DatasetItem>("/datasets/upload", fd)
    },
    onSuccess: (ds) => {
      toast.success("Dataset uploaded")
      setSelected(ds.id)
      queryClient.invalidateQueries({ queryKey: ["datasets"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Upload failed"),
  })

  const train = useMutation({
    mutationFn: (datasetId: number) =>
      api.post<{ best_model: string; models: Record<string, unknown> }>(
        "/models/train",
        { dataset_id: datasetId },
      ),
    onSuccess: (res) => {
      toast.success(`Training complete. Best model: ${res.best_model}`)
      queryClient.invalidateQueries({ queryKey: ["datasets"] })
      queryClient.invalidateQueries({ queryKey: ["models"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Training failed"),
  })

  const handleFile = (f: File | undefined) => {
    if (!f) return
    if (!f.name.endsWith(".csv")) {
      toast.error("Only CSV files are supported")
      return
    }
    upload.mutate(f)
  }

  const statusBadge = (s: string) => {
    const map: Record<string, { variant: "success" | "warning" | "info" | "destructive" | "secondary"; label: string }> = {
      uploaded: { variant: "info", label: "Uploaded" },
      validated: { variant: "warning", label: "Validated" },
      trained: { variant: "success", label: "Trained" },
      failed: { variant: "destructive", label: "Failed" },
    }
    const m = map[s] ?? { variant: "secondary" as const, label: s }
    return <Badge variant={m.variant}>{m.label}</Badge>
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dataset</h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          Upload CSV data, validate it, and train the ML models. Required columns:{" "}
          {REQUIRED_COLUMNS.join(", ")}.
        </p>
      </div>

      <AcademicImport />

      {/* Upload zone */}
      <Card
        className={dragOver ? "border-dashed border-2 border-[var(--primary)]" : ""}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          handleFile(e.dataTransfer.files?.[0])
        }}
      >
        <CardContent className="flex flex-col items-center justify-center gap-3 p-10 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--primary)]/10 text-[var(--primary)]">
            <Upload className="h-7 w-7" />
          </div>
          <div>
            <p className="font-semibold">Drag & drop your CSV here, or browse</p>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              The bundled sample <code className="rounded bg-[var(--muted)] px-1.5 py-0.5 text-xs">data/student_performance.csv</code>{" "}
              (600 synthetic rows) works out of the box.
            </p>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
          <Button onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
            {upload.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {upload.isPending ? "Uploading…" : "Choose CSV file"}
          </Button>
        </CardContent>
      </Card>

      {/* Datasets list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-4 w-4 text-[var(--primary)]" /> Datasets
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : !datasets?.length ? (
            <div className="p-4">
              <EmptyState icon={Database} title="No datasets yet" description="Upload a CSV to get started." />
            </div>
          ) : (
            <div className="divide-y divide-[var(--border)]">
              {datasets.map((d) => (
                <div key={d.id} className="flex flex-wrap items-center gap-3 px-5 py-3.5">
                  <button className="flex flex-1 items-center gap-3 text-left" onClick={() => setSelected(d.id)}>
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--muted)]">
                      <Table2 className="h-4 w-4 text-[var(--muted-foreground)]" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium">{d.name}</p>
                      <p className="text-xs text-[var(--muted-foreground)]">
                        {d.filename} · {d.rows ?? "?"} rows · {d.columns ?? "?"} cols · {formatDateTime(d.created_at)}
                      </p>
                      {d.validation_errors && (
                        <p className="mt-0.5 flex items-center gap-1 text-xs text-red-500">
                          <FileWarning className="h-3 w-3" /> {d.validation_errors.slice(0, 120)}
                        </p>
                      )}
                    </div>
                  </button>
                  {statusBadge(d.status)}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelected(d.id)}
                  >
                    Preview
                  </Button>
                  {d.status !== "trained" && (
                    <Button
                      size="sm"
                      disabled={train.isPending}
                      onClick={() => train.mutate(d.id)}
                    >
                      {train.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <FlaskConical className="h-4 w-4" />
                      )}
                      Train Model
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Validation + preview */}
      {selected !== null && (
        <Card>
          <CardHeader>
            <CardTitle>Dataset Analysis</CardTitle>
            <CardDescription>Validation report and data preview</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {previewLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : preview ? (
              <>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div className="rounded-lg border border-[var(--border)] p-3">
                    <p className="text-xs text-[var(--muted-foreground)]">Rows</p>
                    <p className="text-lg font-bold">{preview.rows}</p>
                  </div>
                  <div className="rounded-lg border border-[var(--border)] p-3">
                    <p className="text-xs text-[var(--muted-foreground)]">Columns</p>
                    <p className="text-lg font-bold">{preview.columns}</p>
                  </div>
                  <div className="rounded-lg border border-[var(--border)] p-3">
                    <p className="text-xs text-[var(--muted-foreground)]">Missing Values</p>
                    <p className="text-lg font-bold">
                      {Object.values(preview.missing_values).reduce((a, b) => a + b, 0)}
                    </p>
                  </div>
                  <div className="rounded-lg border border-[var(--border)] p-3">
                    <p className="text-xs text-[var(--muted-foreground)]">Duplicates</p>
                    <p className="text-lg font-bold">{preview.duplicates}</p>
                  </div>
                </div>

                <div className="rounded-lg border border-[var(--border)] p-4">
                  <p className="mb-2 text-sm font-semibold">Validation</p>
                  {preview.validation_errors.length === 0 ? (
                    <div className="flex items-center gap-2 text-sm text-emerald-500">
                      <CheckCircle2 className="h-4 w-4" />
                      Dataset is valid and ready for training.
                    </div>
                  ) : (
                    <ul className="space-y-1">
                      {preview.validation_errors.map((e, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-red-500">
                          <XCircle className="h-4 w-4 shrink-0" /> {e}
                        </li>
                      ))}
                      <li className="flex items-center gap-2 pt-1 text-xs text-[var(--muted-foreground)]">
                        <AlertTriangle className="h-3.5 w-3.5" /> Fix the issues above — training is blocked until the
                        dataset is valid.
                      </li>
                    </ul>
                  )}
                </div>

                <div className="rounded-lg border border-[var(--border)] p-4">
                  <p className="mb-2 text-sm font-semibold">Preview (first 10 rows)</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[var(--border)] text-left text-[var(--muted-foreground)]">
                          {Object.keys(preview.preview[0] ?? {}).map((c) => (
                            <th key={c} className="px-3 py-2 font-medium">{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.preview.map((row, i) => (
                          <tr key={i} className="border-b border-[var(--border)] last:border-0">
                            {Object.values(row).map((v, j) => (
                              <td key={j} className="px-3 py-1.5">
                                {String(v ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function AcademicImport() {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [report, setReport] = useState<ImportValidationReport | null>(null)

  const { data: history } = useQuery({
    queryKey: ["imports-history"],
    queryFn: () => api.get<ImportHistoryItem[]>("/datasets/imports/history"),
  })

  const validate = useMutation({
    mutationFn: async (f: File) => {
      const fd = new FormData()
      fd.append("file", f)
      return api.post<ImportValidationReport>("/datasets/import/validate", fd)
    },
    onSuccess: (rep) => {
      setReport(rep)
      if (rep.valid_rows === 0) {
        toast.error("No valid rows found — fix the errors and retry")
      } else {
        toast.success(`Validation complete: ${rep.valid_rows} of ${rep.rows} rows are valid`)
      }
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Validation failed"),
  })

  const doImport = useMutation({
    mutationFn: async (f: File) => {
      const fd = new FormData()
      fd.append("file", f)
      return api.post<ImportResult>("/datasets/import", fd)
    },
    onSuccess: (res) => {
      toast.success(`Imported ${res.imported_rows} records (${res.created_students.length} new students)`)
      queryClient.invalidateQueries({ queryKey: ["imports-history"] })
      queryClient.invalidateQueries({ queryKey: ["data-source"] })
      queryClient.invalidateQueries({ queryKey: ["data-sources"] })
      setReport(null)
      setFile(null)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Import failed"),
  })

  const pick = (f: File | undefined) => {
    if (!f) return
    if (!f.name.endsWith(".csv")) {
      toast.error("Only CSV files are supported")
      return
    }
    setFile(f)
    setReport(null)
    validate.mutate(f)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSpreadsheet className="h-4 w-4 text-emerald-500" /> Import Academic Records
        </CardTitle>
        <CardDescription>
          Load approved academic records (students, subjects, internal assessments, assignments,
          attendance) into the platform. Records are validated first — only valid rows are imported.
          Expected columns: student_id, subject, semester, attendance, internal_1, internal_2,
          assignment_score, engagement, target, optionally student_name / department / section / previous_performance.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => pick(e.target.files?.[0])}
          />
          <Button variant="outline" onClick={() => fileRef.current?.click()} disabled={validate.isPending || doImport.isPending}>
            {validate.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {file ? file.name : "Choose academic CSV"}
          </Button>
          {report && (
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="info">{report.rows} total rows</Badge>
              <Badge variant="success">{report.valid_rows} valid</Badge>
              {report.warnings > 0 && <Badge variant="warning">{report.warnings} warnings</Badge>}
              {report.rejected > 0 && <Badge variant="destructive">{report.rejected} rejected</Badge>}
            </div>
          )}
        </div>

        {report && (
          <div className="space-y-4 rounded-lg border border-[var(--border)] p-4">
            {report.will_create_students && (
              <p className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                <AlertTriangle className="h-3.5 w-3.5" />
                Import will auto-create new student accounts for student IDs not present in the database.
              </p>
            )}

            {report.errors.length > 0 && (
              <div>
                <p className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-red-500">
                  <XCircle className="h-4 w-4" /> Errors ({report.errors_total})
                </p>
                <ul className="space-y-1">
                  {report.errors.slice(0, 5).map((e, i) => (
                    <li key={i} className="text-xs text-[var(--muted-foreground)]">{e}</li>
                  ))}
                  {report.error_truncated && (
                    <li className="text-xs text-[var(--muted-foreground)]">… and more errors</li>
                  )}
                </ul>
              </div>
            )}

            {report.preview.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-left text-[var(--muted-foreground)]">
                      {Object.keys(report.preview[0] ?? {}).map((c) => (
                        <th key={c} className="px-3 py-2 font-medium">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.preview.map((row, i) => (
                      <tr key={i} className="border-b border-[var(--border)] last:border-0">
                        {Object.values(row).map((v, j) => (
                          <td key={j} className="px-3 py-1.5">{v == null ? "" : String(v)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {report.valid_rows > 0 && (
              <Button
                disabled={doImport.isPending}
                onClick={() => file && doImport.mutate(file)}
              >
                {doImport.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                {doImport.isPending ? "Importing…" : `Import ${report.valid_rows} valid records`}
              </Button>
            )}
          </div>
        )}

        {history && history.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
              Recent imports
            </p>
            <div className="space-y-1.5">
              {history.slice(0, 5).map((h) => (
                <div key={h.id} className="flex items-center justify-between rounded-md border border-[var(--border)] px-3 py-2 text-xs">
                  <span className="font-medium">{h.name}</span>
                  <span className="text-[var(--muted-foreground)]">
                    {h.rows ?? "?"} rows · {formatDateTime(h.created_at)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
