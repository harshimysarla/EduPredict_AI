import { api } from "@/lib/api"
import type {
  PortalImportResult,
  PortalProfileDetail,
  PortalSemesterDetail,
  PortalSemesterList,
  PortalSubjectRow,
  PortalSummary,
} from "@/types"

/**
 * Portal service — the only frontend surface for the Samvidha-style academic
 * portal data. Components call these typed functions instead of the raw API.
 */
export const portalService = {
  summary: () => api.get<PortalSummary>("/student/me/portal/summary"),

  profile: () => api.get<PortalProfileDetail>("/student/me/portal/profile"),

  semesters: () => api.get<PortalSemesterList>("/student/me/portal/semesters"),

  semester: (sem: number) =>
    api.get<PortalSemesterDetail>(`/student/me/portal/semesters/${sem}`),

  subjects: (params: {
    semester?: number
    search?: string
    courseType?: string
    sortBy?: string
    order?: string
  }) => {
    const qs = new URLSearchParams()
    if (params.semester != null && params.semester > 0) qs.set("semester", String(params.semester))
    if (params.search) qs.set("search", params.search)
    if (params.courseType) qs.set("course_type", params.courseType)
    if (params.sortBy) qs.set("sort_by", params.sortBy)
    if (params.order) qs.set("order", params.order)
    const query = qs.toString()
    return api.get<{ subjects: PortalSubjectRow[]; total: number }>(
      `/student/me/portal/subjects${query ? `?${query}` : ""}`,
    )
  },
}

export const portalAdminService = {
  importCsv: (file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    return api.upload<PortalImportResult>("/admin/portal/import", formData)
  },
}