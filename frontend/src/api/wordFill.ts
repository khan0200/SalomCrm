import apiClient from './client'
import type { CrmField } from './excelFill'

export type WordSlotKind = 'text' | 'checkbox'

export interface WordSlot {
  slot_id: string
  kind: WordSlotKind
  label: string
  current_text: string
  options?: string[]
  existing_placeholder?: string
  table_index?: number
  row?: number
  col?: number
  paragraph_index?: number
}

export interface WordTablePreview {
  table_index: number
  rows: number
  cols: number
  preview_rows: { row_idx: number; values: string[] }[]
}

export interface WordSuggestedMapping {
  slot_id: string
  field: string
  confidence: number
  reason?: string
}

/** Where the suggestions came from: full AI pass, partial AI, or the offline dictionary. */
export type MappingSource = 'ai' | 'ai_partial' | 'fallback'

export interface WordAnalysisResult {
  slots: WordSlot[]
  tables: WordTablePreview[]
  paragraph_count: number
  available_fields: CrmField[]
  suggested_mappings: WordSuggestedMapping[]
  mapping_source: MappingSource
}

/** One approved slot, ready to be written by the backend. */
export interface WordMappingConfig {
  slot_id: string
  kind: WordSlotKind
  label: string
  field: string
  options?: string[]
  existing_placeholder?: string
  static_value?: string
  fallback?: string
  confidence?: number
  reason?: string
  format_rules: {
    dateFormat?: string
    genderFormat?: string
    phoneFormat?: string
    boolFormat?: string
  }
}

export interface AnalyzeWordParams {
  file: File
  use_ai?: boolean
  provider?: string
  model?: string
  api_key?: string
}

export interface GenerateWordParams {
  file: File
  mappings?: WordMappingConfig[]
  custom_tag_mappings?: Record<string, string>
  student_ids: string[]
  filename_pattern?: string
  checkbox_mark?: string
}

export interface WordScannedTag {
  tag_name: string
  raw_tag: string
  occurrences: number
  is_recognized: boolean
  crm_field: string | null
  field_label: string | null
  category: string | null
  category_label: string | null
  sample: string | null
  description: string
}

export interface WordScanTagsResult {
  total_tags_count: number
  unique_tags_count: number
  recognized_count: number
  alien_count: number
  tags: WordScannedTag[]
  available_fields: { key: string; label: string; category: string }[]
}

export interface WordPlaceholderField {
  key: string
  label: string
  category: string
  category_label: string
  icon?: string
  primary_tag: string
  aliases: string[]
  sample: string
  description: string
  is_common?: boolean
}

export const wordFillApi = {
  getPlaceholderCatalog: async (): Promise<WordPlaceholderField[]> => {
    const response = await apiClient.get<WordPlaceholderField[]>('/students/word-fill/fields/')
    return response.data
  },

  scanTags: async (file: File): Promise<WordScanTagsResult> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<WordScanTagsResult>(
      '/students/word-fill/scan-tags/',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },

  downloadExampleTemplate: async (): Promise<Blob> => {
    const response = await apiClient.get('/students/word-fill/example/', {
      responseType: 'blob',
    })
    return response.data
  },

  analyzeTemplate: async (params: AnalyzeWordParams): Promise<WordAnalysisResult> => {
    const formData = new FormData()
    formData.append('file', params.file)
    formData.append('use_ai', String(params.use_ai ?? true))
    if (params.provider) formData.append('provider', params.provider)
    if (params.model) formData.append('model', params.model)
    if (params.api_key) formData.append('api_key', params.api_key)

    const response = await apiClient.post<WordAnalysisResult>(
      '/students/word-fill/analyze/',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },

  generateFilledWord: async (params: GenerateWordParams): Promise<Blob> => {
    const formData = new FormData()
    formData.append('file', params.file)
    if (params.mappings && params.mappings.length > 0) {
      formData.append('mappings', JSON.stringify(params.mappings))
    }
    if (params.custom_tag_mappings && Object.keys(params.custom_tag_mappings).length > 0) {
      formData.append('custom_tag_mappings', JSON.stringify(params.custom_tag_mappings))
    }
    formData.append('student_ids', JSON.stringify(params.student_ids))
    formData.append('filename_pattern', params.filename_pattern || 'APPFORM_{full_name}')
    formData.append('checkbox_mark', params.checkbox_mark || 'V')

    const response = await apiClient.post(
      '/students/word-fill/generate/',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
      }
    )
    return response.data
  },
}

