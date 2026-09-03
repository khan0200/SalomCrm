import apiClient from './client'

export interface ExcelColumn {
  col_idx: number
  col_letter: string
  header_name: string
  is_hidden: boolean
  suggested_field: string
  confidence: number
  sample_value?: string
}

export interface ExcelSheet {
  name: string
  max_row: number
  max_column: number
  detected_header_row: number
  columns: ExcelColumn[]
  preview_rows: { row_idx: number; values: string[] }[]
}

export interface CrmField {
  key: string
  label: string
  category: string
  description?: string
}

export interface ExcelAnalysisResult {
  sheets: ExcelSheet[]
  available_fields: CrmField[]
}

export interface ColumnMappingConfig {
  col_idx: number
  col_letter: string
  header_name: string
  field: string
  static_value?: string
  fallback?: string
  format_rules: {
    dateFormat?: string
    genderFormat?: string
    phoneFormat?: string
    boolFormat?: string
  }
}

export interface GenerateFilledExcelParams {
  file: File
  sheet_name: string
  column_mappings: ColumnMappingConfig[]
  student_ids: string[]
  fill_mode: 'append' | 'overwrite'
  start_row?: number
  auto_increment_sequence?: boolean
}

export const excelFillApi = {
  analyzeTemplate: async (file: File): Promise<ExcelAnalysisResult> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<ExcelAnalysisResult>(
      '/students/excel-fill/analyze/',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  generateFilledExcel: async (params: GenerateFilledExcelParams): Promise<Blob> => {
    const formData = new FormData()
    formData.append('file', params.file)
    formData.append('sheet_name', params.sheet_name)
    formData.append('fill_mode', params.fill_mode)
    formData.append('auto_increment_sequence', String(params.auto_increment_sequence ?? true))
    if (params.start_row) {
      formData.append('start_row', String(params.start_row))
    }
    formData.append('column_mappings', JSON.stringify(params.column_mappings))
    formData.append('student_ids', JSON.stringify(params.student_ids))

    const response = await apiClient.post(
      '/students/excel-fill/generate/',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
      }
    )
    return response.data
  },
}
