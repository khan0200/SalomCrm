export type CanvasElementType =
  | 'text'
  | 'heading'
  | 'paragraph'
  | 'table'
  | 'signature'
  | 'line'
  | 'checkbox'
  | 'date'
  | 'variable'
  | 'image'

export interface PageMargins {
  top: number // mm
  right: number // mm
  bottom: number // mm
  left: number // mm
}

export interface TextStyleProps {
  fontFamily?: string
  fontSize?: number // pt
  fontWeight?: string | number // 'normal' | 'bold' | 400 | 700
  fontStyle?: 'normal' | 'italic'
  textDecoration?: 'none' | 'underline' | 'line-through'
  color?: string
  backgroundColor?: string
  textAlign?: 'left' | 'center' | 'right' | 'justify'
  lineHeight?: number
  letterSpacing?: number // pt or mm
  padding?: number // mm
}

export interface BaseCanvasElement {
  id: string
  type: CanvasElementType
  x: number // mm from top-left of page
  y: number // mm from top-left of page
  width: number // mm
  height: number // mm
  rotation?: number // degrees (default 0)
  zIndex: number
  locked?: boolean
  hidden?: boolean
}

export interface TextCanvasElement extends BaseCanvasElement {
  type: 'text' | 'heading' | 'paragraph' | 'date' | 'variable'
  content: string // HTML or formatted string
  style: TextStyleProps
  variableKey?: string // e.g., '{{client_name}}'
  headingLevel?: 1 | 2 | 3
}

export interface TableCellModel {
  id: string
  content: string // cell HTML or text
  rowSpan?: number
  colSpan?: number
  backgroundColor?: string
  color?: string
  textAlign?: 'left' | 'center' | 'right' | 'justify'
  verticalAlign?: 'top' | 'middle' | 'bottom'
  fontWeight?: string | number
  fontSize?: number
  borders?: {
    top?: string
    bottom?: string
    left?: string
    right?: string
  }
}

export interface TableCanvasElement extends BaseCanvasElement {
  type: 'table'
  rows: number
  cols: number
  colWidths: number[] // width of each column in mm (sum should equal width)
  rowHeights: number[] // min height of each row in mm (sum should approximate height)
  cells: TableCellModel[][] // 2D array [row][col]
  borderWidth?: string
  borderColor?: string
  borderStyle?: string
  density?: 'compact' | 'normal' | 'spacious'
}

export interface SignatureCanvasElement extends BaseCanvasElement {
  type: 'signature'
  signerRole: 'dual' | 'bajaruvchi' | 'mijoz'
  contractorTitle?: string
  contractorCompany?: string
  contractorDirector?: string
  contractorInn?: string
  contractorAddress?: string
  contractorPhone?: string
  contractorAccount?: string
  clientName?: string
  clientPassport?: string
  clientAddress?: string
  clientPhone?: string
  clientBirthDate?: string
  signedDate?: string
  showStampArea?: boolean
}

export interface LineCanvasElement extends BaseCanvasElement {
  type: 'line'
  orientation: 'horizontal' | 'vertical'
  strokeWidth: number // mm or pt
  strokeColor: string
  strokeStyle: 'solid' | 'dashed' | 'dotted'
}

export interface CheckboxCanvasElement extends BaseCanvasElement {
  type: 'checkbox'
  checked: boolean
  label: string
  fontSize?: number
  color?: string
}

export interface ImageCanvasElement extends BaseCanvasElement {
  type: 'image'
  src: string
  objectFit?: 'contain' | 'cover' | 'fill'
  opacity?: number
}

export type CanvasElement =
  | TextCanvasElement
  | TableCanvasElement
  | SignatureCanvasElement
  | LineCanvasElement
  | CheckboxCanvasElement
  | ImageCanvasElement

export interface CanvasPageModel {
  id: string
  pageNumber: number
  elements: CanvasElement[]
}

export interface ContractDocumentModel {
  version: 2
  type: 'canvas-contract'
  pageSize: {
    width: number // 210 mm
    height: number // 297 mm
    unit: 'mm'
  }
  margins: PageMargins
  pages: CanvasPageModel[]
  defaultFontFamily?: string
  defaultFontSize?: number
}

// Coordinate & transformation helper types
export type ResizeHandle = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w'

export interface AlignmentGuide {
  type: 'horizontal' | 'vertical'
  position: number // mm coordinate
  start: number // mm
  end: number // mm
  label?: string
}

export interface BoundingBox {
  x: number // mm
  y: number // mm
  width: number // mm
  height: number // mm
}
