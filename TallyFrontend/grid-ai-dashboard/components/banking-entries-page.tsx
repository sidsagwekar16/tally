"use client"

import type React from "react"
import { useEffect } from "react"
import { useState } from "react"
import { Bot, Upload, Search, Download, Trash2, CheckCircle, Edit, Plus, ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { format } from "date-fns"
import { CreateLedgerDialog } from "./create-ledger-dialog"
import { EditNarrationDialog } from "./edit-narration-dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { UploadBankStatementDialog } from "./upload-bank-statement-dialog"



// Mock data for ledgers
const initialLedgers = [
  { id: "l1", name: "Salary Account", parentGroup: "Income (Direct)" },
  { id: "l2", name: "Office Expenses", parentGroup: "Expenses (Indirect)" },

]

// Mock data for files
const mockFile = {
  id: 1,
  name: "bank_statement_april_2024.pdf",
  uploadDate: "2024-04-15 14:30",
  uploadedBy: "John Doe",
  bankLedger: "HDFC Bank",
  dateRange: "01-04-2024 - 15-04-2024",
  status: "In Review",
  entries: 7,
  resolved: 3,
  pending: 4,
}

export function BankingEntriesPage() {
  const [transactions, setTransactions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [ledgers, setLedgers] = useState<any[]>([])
  const [ledgersLoading, setLedgersLoading] = useState(true)
const [ledgersError, setLedgersError] = useState<string | null>(null)


  const [selectedFile, setSelectedFile] = useState(mockFile)
  const [selectedTransactions, setSelectedTransactions] = useState<number[]>([])
  const [filters, setFilters] = useState({
    date: "",
    narration: "",
    amount: "",
    type: "all", // Updated default value
    voucher: "all", // Updated default value
    ledger: "all-ledgers", // Updated default value
    status: "all", // Updated default value
  })
  const [dateRange, setDateRange] = useState<{ from: Date | undefined; to: Date | undefined }>({
    from: undefined,
    to: undefined,
  })
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false)
  const [isCreateLedgerOpen, setIsCreateLedgerOpen] = useState(false)
  const [editingNarration, setEditingNarration] = useState<{
    open: boolean
    transaction: any | null
  }>({
    open: false,
    transaction: null,
  })
  const [deleteConfirmation, setDeleteConfirmation] = useState<{
    open: boolean
    transactionId: number | null
  }>({
    open: false,
    transactionId: null,
  })
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)

  // Filter transactions based on current filters
  const filteredTransactions = transactions.filter((transaction) => {
    return (
      (filters.date ? transaction.date.includes(filters.date) : true) &&
      (filters.narration ? transaction.narration.toLowerCase().includes(filters.narration.toLowerCase()) : true) &&
      (filters.amount ? transaction.amount.toString().includes(filters.amount) : true) &&
      (filters.type === "all" || transaction.type === filters.type) &&
      (filters.voucher === "all" || transaction.voucher === filters.voucher) &&
      (filters.ledger === "all-ledgers" || transaction.ledger === filters.ledger) &&
      (filters.status === "all" || transaction.status === filters.status)
    )
  })

useEffect(() => {
  setCurrentPage(1)
}, [filters, transactions])



const [currentPage, setCurrentPage] = useState(1)
const [pageSize, setPageSize] = useState(10) // Show 10 per page by default

// Calculate total pages
const totalPages = Math.ceil(filteredTransactions.length / pageSize)

// Slice transactions for the current page
const paginatedTransactions = filteredTransactions.slice(
  (currentPage - 1) * pageSize,
  currentPage * pageSize
)

  // Handle select all checkbox
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedTransactions(filteredTransactions.map((t) => t.id))
    } else {
      setSelectedTransactions([])
    }
  }

  // Handle individual checkbox selection
  const handleSelectTransaction = (checked: boolean, id: number) => {
    if (checked) {
      setSelectedTransactions([...selectedTransactions, id])
    } else {
      setSelectedTransactions(selectedTransactions.filter((transactionId) => transactionId !== id))
    }
  }

  // Handle transaction type change (Dr/Cr)
  const handleTypeChange = (value: string, transactionId: number) => {
    setTransactions(
      transactions.map((transaction) => {
        if (transaction.id === transactionId) {
          // Reset voucher type based on new Dr/Cr value
          let newVoucher = transaction.voucher
          if (value === "Dr" && !["Payment", "Contra", "Journal"].includes(transaction.voucher)) {
            newVoucher = "Payment"
          } else if (value === "Cr" && !["Receipt", "Contra", "Journal"].includes(transaction.voucher)) {
            newVoucher = "Receipt"
          }

          return {
            ...transaction,
            type: value,
            voucher: newVoucher,
          }
        }
        return transaction
      }),
    )
  }

  // Handle voucher type change
  const handleVoucherChange = (value: string, transactionId: number) => {
    setTransactions(
      transactions.map((transaction) => {
        if (transaction.id === transactionId) {
          return {
            ...transaction,
            voucher: value,
          }
        }
        return transaction
      }),
    )
  }

  // Handle ledger change
  const handleLedgerChange = (value: string, transactionId: number) => {
    setTransactions(
      transactions.map((transaction) => {
        if (transaction.id === transactionId) {
          return {
            ...transaction,
            ledger: value,
          }
        }
        return transaction
      }),
    )
  }

  // Handle create new ledger
  const handleCreateLedger = (newLedger: any) => {
    setLedgers([...ledgers, newLedger])
  }

  // Handle edit narration
  const handleEditNarration = (transaction: any) => {
    setEditingNarration({
      open: true,
      transaction,
    })
  }

  // Handle save narration
  const handleSaveNarration = (narration: string, remark: string) => {
    if (!editingNarration.transaction) return

    setTransactions(
      transactions.map((transaction) => {
        if (transaction.id === editingNarration.transaction.id) {
          return {
            ...transaction,
            narration,
            remark,
          }
        }
        return transaction
      }),
    )
  }

  // Handle delete transaction
  const handleDeleteTransaction = (transactionId: number) => {
    setDeleteConfirmation({
      open: true,
      transactionId,
    })
  }

  // Confirm delete transaction
  const confirmDeleteTransaction = () => {
    if (!deleteConfirmation.transactionId) return

    setTransactions(transactions.filter((t) => t.id !== deleteConfirmation.transactionId))
    setSelectedTransactions(selectedTransactions.filter((id) => id !== deleteConfirmation.transactionId))
    setDeleteConfirmation({ open: false, transactionId: null })
  }

  function formatDate(date: string) {
  if (!date) return ""
  const [y, m, d] = date.split("-")
  return `${d}-${m}-${y}`
}

useEffect(() => {
  async function fetchLedgers() {
    try {
      const res = await fetch(
        "http://127.0.0.1:8000/ledgers/by-company/bde757d0-7b46-4b01-a80d-ddcecdc0d6cc"

      )
      if (!res.ok) throw new Error("Failed to fetch ledgers")
      const data = await res.json()
      // Map data if your backend returns extra fields or uses different names
      const mapped = data.map((ledger: any) => ({
        id: ledger.id,
        name: ledger.name,
        parentGroup: ledger.parent_group || "", // Adjust as per your API response
      }))
      setLedgers(mapped)
    } catch (err: any) {
      // Optionally, handle error UI or fallback to empty
      setLedgers([])
    }
  }
  fetchLedgers()
}, [])


  useEffect(() => {
  async function fetchTransactions() {
    try {
      setLoading(true)
      const res = await fetch(
        "http://127.0.0.1:8000/transactions?statement_id=99d3db42-d2c5-4b19-b841-71c1272efd2a"
      )
      if (!res.ok) throw new Error("Failed to fetch transactions")
      const data = await res.json()
      // Map API response to your UI shape
      const mapped = data.map((tx: any) => ({
        id: tx.id,
        date: formatDate(tx.date), // Converts to DD-MM-YYYY
        narration: tx.narration,
        amount: tx.withdrawal_amount > 0 ? tx.withdrawal_amount : tx.deposit_amount,
        type: tx.withdrawal_amount > 0 ? "Dr" : "Cr",
        voucher: tx.voucher || "",
        ledger:  tx.to_ledger || "",
        status: tx.status || "Pending",
        remark: "", // UI supports editing/adding this
      }))
      setTransactions(mapped)
      setLoading(false)
    } catch (err: any) {
      setError(err.message || "Error loading transactions")
      setLoading(false)
    }
  }
  fetchTransactions()
}, [])


  // Get available voucher types based on transaction type
  const getVoucherOptions = (type: string) => {
    if (type === "Dr") {
      return ["Payment", "Contra", "Journal"]
    } else if (type === "Cr") {
      return ["Receipt", "Contra", "Journal"]
    }
    return ["Payment", "Receipt", "Contra", "Journal"]
  }

  
  if (loading) return <div className="p-8 text-center text-lg">Loading transactions…</div>
if (error) return <div className="p-8 text-center text-red-600">{error}</div>


  return (
    
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        
        <div>
          <h1 className="text-3xl font-bold">Banking Entries</h1>
          <p className="text-muted-foreground">Manage and process bank statements</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Bot className="h-4 w-4 mr-2" />
            AI Templates
          </Button>
          <Button onClick={() => setIsUploadDialogOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Files</TabsTrigger>
          <TabsTrigger value="review">In Review</TabsTrigger>
          <TabsTrigger value="fixed">Issue Fixed</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Document Review: {selectedFile.name}</CardTitle>
                  <CardDescription>
                    Bank Ledger: {selectedFile.bankLedger} • {selectedFile.dateRange}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                 <Button
  variant="outline"
  onClick={async () => {
    try {
      // Prepare bulk update payload
      const payload = transactions.map((txn) => ({
        id: txn.id,
        withdrawal_amount: txn.type === "Dr" ? txn.amount : 0,
        deposit_amount: txn.type === "Cr" ? txn.amount : 0,
        from_ledger: selectedFile.bankLedger,
        to_ledger: txn.ledger,   
        voucher: txn.voucher, // Note: PATCH endpoint expects 'voucher_type'
        status: txn.status,
        narration: txn.narration,
        remark: txn.remark,
        
      }));

      // Bulk PATCH
      const res = await fetch("http://localhost:8000/transactions/bulk", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Bulk update failed!");
      alert("All changes saved!");
    } catch (err) {
      alert("Failed to save!");
      console.error(err);
    }
  }}
>
  <Download className="h-4 w-4 mr-2" />
  Save
</Button>

                  <Button variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                  <Button>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Send to Tally
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                  <CardContent className="p-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{selectedFile.pending}</div>
                      <div className="text-sm text-muted-foreground">Pending</div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{selectedFile.resolved}</div>
                      <div className="text-sm text-muted-foreground">Resolved</div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{selectedFile.entries}</div>
                      <div className="text-sm text-muted-foreground">Total</div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Bot className="h-8 w-8" />
                      <div>
                        <h3 className="font-bold">AI Recommendations</h3>
                        <p className="text-sm opacity-90">Smart suggestions for faster processing</p>
                      </div>
                    </div>
                    <Badge variant="secondary">3 Available</Badge>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent>
                  <div className="flex items-center justify-between mt-4">
  <div className="flex gap-2 items-center">
    <span>Rows per page:</span>
    <Select value={String(pageSize)} onValueChange={v => { setPageSize(Number(v)); setCurrentPage(1); }}>
      <SelectTrigger className="w-[70px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {[10, 20, 50, 100].map(size => (
          <SelectItem key={size} value={String(size)}>{size}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  </div>
  <div className="flex gap-4 items-center">
    <Button variant="ghost" disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)}>
      Prev
    </Button>
    <span>
      Page <b>{currentPage}</b> of <b>{totalPages}</b>
    </span>
    <Button variant="ghost" disabled={currentPage === totalPages || totalPages === 0} onClick={() => setCurrentPage(p => p + 1)}>
      Next
    </Button>
  </div>
</div>

                </CardContent>
              </Card>

              <Tabs defaultValue="all" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="all">All</TabsTrigger>
                  <TabsTrigger value="pending">Pending</TabsTrigger>
                  <TabsTrigger value="resolved">Resolved</TabsTrigger>
                  <TabsTrigger value="deleted">Deleted</TabsTrigger>
                </TabsList>

                <div className="flex flex-wrap items-center gap-4 mb-4">
                  {/* Date Range Filter */}
                  <div className="relative">
                    <Popover open={isDatePickerOpen} onOpenChange={setIsDatePickerOpen}>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-[240px] justify-start text-left font-normal">
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {dateRange.from ? (
                            dateRange.to ? (
                              <>
                                {format(dateRange.from, "dd-MM-yyyy")} - {format(dateRange.to, "dd-MM-yyyy")}
                              </>
                            ) : (
                              format(dateRange.from, "dd-MM-yyyy")
                            )
                          ) : (
                            <span>Date Range</span>
                          )}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          initialFocus
                          mode="range"
                          defaultMonth={dateRange.from}
                          selected={dateRange}
                          onSelect={setDateRange}
                          numberOfMonths={2}
                        />
                      </PopoverContent>
                    </Popover>
                  </div>

                  {/* Narration Filter */}
                  <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Filter by narration..."
                      className="pl-10"
                      value={filters.narration}
                      onChange={(e) => setFilters({ ...filters, narration: e.target.value })}
                    />
                  </div>

                  {/* Amount Filter */}
                  <Input
                    placeholder="Amount"
                    className="w-[120px]"
                    value={filters.amount}
                    onChange={(e) => setFilters({ ...filters, amount: e.target.value })}
                  />

                  {/* Type Filter */}
                  <Select value={filters.type} onValueChange={(value) => setFilters({ ...filters, type: value })}>
                    <SelectTrigger className="w-[100px]">
                      <SelectValue placeholder="Dr/Cr" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="Dr">Dr</SelectItem>
                      <SelectItem value="Cr">Cr</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Voucher Filter */}
                  <Select value={filters.voucher} onValueChange={(value) => setFilters({ ...filters, voucher: value })}>
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder="Voucher" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="Payment">Payment</SelectItem>
                      <SelectItem value="Receipt">Receipt</SelectItem>
                      <SelectItem value="Contra">Contra</SelectItem>
                      <SelectItem value="Journal">Journal</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Ledger Filter */}
                  <Select value={filters.ledger} onValueChange={(value) => setFilters({ ...filters, ledger: value })}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Ledger" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        {ledgers.map((ledger) => (
                          <SelectItem key={ledger.id} value={ledger.name}>
                            {ledger.name}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                      <div className="border-t border-gray-200 my-1"></div>
                      <div
                        className="flex items-center gap-2 px-2 py-1.5 text-sm text-purple-600 font-medium cursor-pointer hover:bg-purple-50 rounded-sm"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          setIsCreateLedgerOpen(true)
                        }}
                      >
                        <Plus className="h-3 w-3" />
                        Create New Ledger
                      </div>
                    </SelectContent>
                  </Select>

                  {/* Status Filter */}
                  <Select value={filters.status} onValueChange={(value) => setFilters({ ...filters, status: value })}>
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="Pending">Pending</SelectItem>
                      <SelectItem value="Resolved">Resolved</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Clear Filters */}
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setFilters({
                        date: "",
                        narration: "",
                        amount: "",
                        type: "all",
                        voucher: "all",
                        ledger: "all-ledgers",
                        status: "all",
                      })
                      setDateRange({ from: undefined, to: undefined })
                    }}
                  >
                    Clear Filters
                  </Button>
                </div>

                <Card>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">
                          <Checkbox
                            checked={
                              filteredTransactions.length > 0 &&
                              selectedTransactions.length === filteredTransactions.length
                            }
                            onCheckedChange={handleSelectAll}
                          />
                        </TableHead>
                        <TableHead>
                          <div className="flex items-center gap-1">
                            No
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead>
                          <div className="flex items-center gap-1">
                            Date
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead>
                          <div className="flex items-center gap-1">
                            Narration
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead>
                          <div className="flex items-center gap-1">
                            Amount
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead>Dr/Cr</TableHead>
                        <TableHead>Voucher</TableHead>
                        <TableHead>Ledger</TableHead>
                        <TableHead>
                          <div className="flex items-center gap-1">
                            Status
                            <ArrowUpDown className="h-3 w-3" />
                          </div>
                        </TableHead>
                        <TableHead>Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                     {paginatedTransactions.map((transaction) => (

                        <TableRow key={transaction.id}>
                          <TableCell>
                            <Checkbox
                              checked={selectedTransactions.includes(transaction.id)}
                              onCheckedChange={(checked) => handleSelectTransaction(!!checked, transaction.id)}
                            />
                          </TableCell>
                          <TableCell>{transaction.id}</TableCell>
                          <TableCell>{transaction.date}</TableCell>
                          <TableCell className="max-w-xs">
                            <div className="flex items-center gap-2">
                              <div className="truncate">{transaction.narration}</div>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => handleEditNarration(transaction)}
                              >
                                <Edit className="h-3 w-3" />
                              </Button>
                            </div>
                            {transaction.remark && (
                              <div className="text-xs text-muted-foreground mt-1">Remark: {transaction.remark}</div>
                            )}
                          </TableCell>
                          <TableCell className="font-medium">₹{transaction.amount.toLocaleString()}</TableCell>
                          <TableCell>
                            <Select
                              value={transaction.type}
                              onValueChange={(value) => handleTypeChange(value, transaction.id)}
                            >
                              <SelectTrigger className="w-[70px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Dr">Dr</SelectItem>
                                <SelectItem value="Cr">Cr</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Select
                              value={transaction.voucher}
                              onValueChange={(value) => handleVoucherChange(value, transaction.id)}
                            >
                              <SelectTrigger className="w-[100px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {getVoucherOptions(transaction.type).map((voucher) => (
                                  <SelectItem key={voucher} value={voucher}>
                                    {voucher}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Select
                              value={transaction.ledger}
                              onValueChange={(value) => {
                                if (value === "create-new") {
                                  setIsCreateLedgerOpen(true)
                                } else {
                                  handleLedgerChange(value, transaction.id)
                                }
                              }}
                            >
                              <SelectTrigger className="w-[160px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectGroup>
                                  {ledgers.map((ledger) => (
                                    <SelectItem key={ledger.id} value={ledger.name}>
                                      {ledger.name}
                                    </SelectItem>
                                  ))}
                                </SelectGroup>
                                <div className="border-t border-gray-200 my-1"></div>
                                <SelectItem value="create-new" className="text-purple-600 font-medium">
                                  <div className="flex items-center gap-1">
                                    <Plus className="h-3 w-3" />
                                    Create New Ledger
                                  </div>
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={transaction.status === "Resolved" ? "default" : "secondary"}
                              className={transaction.status === "Resolved" ? "bg-green-600" : ""}
                            >
                              {transaction.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0 text-red-600"
                                onClick={() => handleDeleteTransaction(transaction.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              </Tabs>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Ledger Dialog */}
      <CreateLedgerDialog
        open={isCreateLedgerOpen}
        onOpenChange={setIsCreateLedgerOpen}
        onCreateLedger={handleCreateLedger}
      />

      {/* Edit Narration Dialog */}
      {editingNarration.transaction && (
        <EditNarrationDialog
          open={editingNarration.open}
          onOpenChange={(open) => setEditingNarration({ ...editingNarration, open })}
          narration={editingNarration.transaction.narration}
          remark={editingNarration.transaction.remark}
          onSave={handleSaveNarration}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={deleteConfirmation.open}
        onOpenChange={(open) => setDeleteConfirmation({ ...deleteConfirmation, open })}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the selected transaction.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeleteTransaction} className="bg-red-600 hover:bg-red-700">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Upload Bank Statement Dialog */}
      <UploadBankStatementDialog
        open={isUploadDialogOpen}
        onOpenChange={setIsUploadDialogOpen}
        onUpload={(fileData) => {
          console.log("File uploaded:", fileData)
          // Here you would typically send the file to your backend
          // For now, we'll just log it and show a success message
          alert(`Successfully uploaded ${fileData.file.name} for ${fileData.bankName}`)
        }}
      />
    </div>
  )
}

// Calendar icon component
function CalendarIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
      <line x1="16" x2="16" y1="2" y2="6" />
      <line x1="8" x2="8" y1="2" y2="6" />
      <line x1="3" x2="21" y1="10" y2="10" />
    </svg>
  )
}
