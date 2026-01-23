import { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown, ChevronUp, ChevronsUpDown, Search } from 'lucide-react'
import { Input } from './Input'
import { Skeleton } from './Skeleton'

export interface Column<T> {
  key: string
  header: string
  sortable?: boolean
  width?: string
  render?: (row: T) => ReactNode
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (row: T) => string | number
  onRowClick?: (row: T) => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  onSort?: (column: string) => void
  searchable?: boolean
  searchValue?: string
  onSearchChange?: (value: string) => void
  searchPlaceholder?: string
  loading?: boolean
  emptyMessage?: string
  className?: string
}

export function DataTable<T extends object>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  sortColumn,
  sortDirection,
  onSort,
  searchable = false,
  searchValue = '',
  onSearchChange,
  searchPlaceholder = 'Search...',
  loading = false,
  emptyMessage = 'No data found',
  className,
}: DataTableProps<T>) {
  const renderSortIcon = (column: Column<T>) => {
    if (!column.sortable) return null

    if (sortColumn === column.key) {
      return sortDirection === 'asc' ? (
        <ChevronUp className="h-4 w-4" />
      ) : (
        <ChevronDown className="h-4 w-4" />
      )
    }

    return <ChevronsUpDown className="h-4 w-4 opacity-50" />
  }

  const getCellValue = (row: T, column: Column<T>): ReactNode => {
    if (column.render) {
      return column.render(row)
    }
    const value = (row as Record<string, unknown>)[column.key]
    if (value === null || value === undefined) return '-'
    return String(value)
  }

  return (
    <div className={cn('rounded-xl bg-gray-900 border border-gray-800 overflow-hidden', className)}>
      {/* Search bar */}
      {searchable && (
        <div className="p-4 border-b border-gray-800">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <Input
              value={searchValue}
              onChange={(e) => onSearchChange?.(e.target.value)}
              placeholder={searchPlaceholder}
              className="pl-10"
            />
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-800/50">
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    'px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider',
                    column.sortable && 'cursor-pointer hover:text-white transition-colors',
                    column.width
                  )}
                  onClick={() => column.sortable && onSort?.(column.key)}
                >
                  <div className="flex items-center gap-1">
                    {column.header}
                    {renderSortIcon(column)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-800 last:border-0">
                  {columns.map((column) => (
                    <td key={column.key} className="px-4 py-3">
                      <Skeleton className="h-4 w-full" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              // Empty state
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-gray-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              // Data rows
              data.map((row) => (
                <tr
                  key={keyExtractor(row)}
                  className={cn(
                    'border-b border-gray-800 last:border-0',
                    'transition-colors',
                    onRowClick && 'cursor-pointer hover:bg-gray-800/50'
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={cn('px-4 py-3 text-sm text-gray-300', column.width)}
                    >
                      {getCellValue(row, column)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
