"use client"
import { useEffect, useState } from "react"
import {
  Bot,
  Upload,
  Search,
  Download,
  Eye,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Zap,
  Filter,
  MoreVertical,
  Star,
  FolderOpen,
  Users,
  Activity,
  TrendingUp,
  ArrowRight,
  Layers,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { UploadBankStatementDialog } from "./upload-bank-statement-dialog"



interface BankingFilesPageProps {
  onReviewFile: (file: any) => void
}

export function BankingFilesPage({ onReviewFile }: BankingFilesPageProps) {
   const [files, setFiles] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)
  const [selectedStatus, setSelectedStatus] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedBank, setSelectedBank] = useState("all")


  useEffect(() => {
    async function fetchStatements() {
      setLoading(true)
      try {
        const res = await fetch("http://localhost:8000/bank-statements") // <--- update your API endpoint as needed
        const data = await res.json()
        // Optional: Map backend fields to your UI fields here
        const mapped = data.map((s: any) => ({
          id: s.id,
          name: `${s.bank_name}_Statement_${s.statement_date}.pdf`, // or use actual filename if available
          uploadDate: s.created_at,
          uploadedBy: s.uploaded_by || "User", // adjust as per backend response
          bankLedger: s.bank_name, // or s.ledger_name if available
          bankName: s.bank_name,
          dateRange: s.statement_date, // adjust as per your API
          status: "Processing", // or s.status if stored
          entries: s.entries || 0, // adjust if your API returns count
          resolved: s.resolved || 0,
          pending: s.pending || 0,
          fileSize: s.file_size || "N/A",
          processingProgress: s.progress || 0,
          priority: "medium", // backend can set
          tags: [],
          color: "bg-blue-500", // set color if you want
        }))
        setFiles(mapped)
      } catch (e) {
        setFiles([])
      }
      setLoading(false)
    }
    fetchStatements()
  }, [])

    if (loading) return <div className="p-8 text-center">Loading bank statements...</div>


  // Filter files
  const filteredFiles = files.filter((file) => {
    return (
      (selectedStatus === "all" || file.status === selectedStatus) &&
      (searchQuery === "" || file.name.toLowerCase().includes(searchQuery.toLowerCase())) &&
      (selectedBank === "all" || file.bankName === selectedBank)
    )
  })

  // Get unique bank names
  const uniqueBanks = Array.from(new Set(files.map((file) => file.bankName)))

  // Status counts
  const statusCounts = files.reduce(
    (acc, file) => {
      acc[file.status] = (acc[file.status] || 0) + 1
      return acc
    },
    {} as Record<string, number>,
  )

  const handleUpload = (fileData: any) => {
    const newFile = {
      id: files.length + 1,
      name: fileData.file.name,
      uploadDate: new Date().toISOString(),
      uploadedBy: "Current User",
      bankLedger: fileData.bankLedger,
      bankName: fileData.bankName,
      dateRange:
        fileData.startDate && fileData.endDate
          ? `${fileData.startDate.toLocaleDateString()} to ${fileData.endDate.toLocaleDateString()}`
          : "Full Statement",
      status: "Processing",
      entries: Math.floor(Math.random() * 200) + 50,
      resolved: 0,
      pending: Math.floor(Math.random() * 200) + 50,
      fileSize: `${(Math.random() * 5 + 0.5).toFixed(1)} MB`,
      processingProgress: 0,
      priority: "medium",
      tags: ["monthly", "new"],
      color: "bg-blue-500",
    }
    setFiles([newFile, ...files])
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Completed":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />
      case "Processing":
        return <Clock className="h-5 w-5 text-blue-600" />
      case "Review Required":
        return <AlertCircle className="h-5 w-5 text-orange-600" />
      case "Failed":
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <FileText className="h-5 w-5 text-gray-500" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <div className="space-y-8">
      {/* Top Section - Header & Quick Actions */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left: Header */}
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl shadow-lg">
              <Layers className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">File Manager</h1>
              <p className="text-gray-600 text-lg">Process bank statements with intelligent automation</p>
            </div>
          </div>

          {/* Quick Stats Row */}
          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>{statusCounts.Completed || 0} Completed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>{statusCounts.Processing || 0} Processing</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
              <span>{statusCounts["Review Required"] || 0} Need Review</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span>{statusCounts.Failed || 0} Failed</span>
            </div>
          </div>
        </div>

        {/* Right: Action Buttons */}
        <div className="flex items-start gap-3">
          <Button variant="outline" className="gap-2 h-12 px-6">
            <Bot className="h-5 w-5" />
            AI Assistant
          </Button>
          <Button
            onClick={() => setIsUploadDialogOpen(true)}
            className="gap-2 h-12 px-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg"
          >
            <Upload className="h-5 w-5" />
            Upload Files
          </Button>
        </div>
      </div>

      {/* AI Insights Panel */}
      <Card className="border-0 shadow-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white overflow-hidden relative">
        <div className="absolute inset-0 bg-black/10"></div>
        <CardContent className="p-8 relative z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="p-4 bg-white/20 rounded-2xl backdrop-blur-sm">
                <Zap className="h-10 w-10" />
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-2">Intelligent Processing Active</h3>
                <p className="text-indigo-100 text-lg">
                  Advanced AI algorithms are analyzing your documents for optimal accuracy
                </p>
                <div className="flex items-center gap-4 mt-3">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    <span className="text-sm">96.8% Accuracy</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    <span className="text-sm">Real-time Processing</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="text-right">
              <Badge variant="secondary" className="bg-white/20 text-white border-white/30 mb-3">
                5 Insights Available
              </Badge>
              <br />
              <Button variant="secondary" className="bg-white/20 hover:bg-white/30 text-white border-white/30">
                View Details
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Control Panel */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left: Filters */}
        <div className="lg:w-80">
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Filter className="h-5 w-5" />
                Filter & Search
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search files..."
                  className="pl-10 border-gray-300 focus:border-purple-500 focus:ring-purple-500"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Status Filter */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-700">Status</label>
                <div className="space-y-2">
                  {[
                    { key: "all", label: "All Files", count: files.length },
                    { key: "Completed", label: "Completed", count: statusCounts.Completed || 0 },
                    { key: "Processing", label: "Processing", count: statusCounts.Processing || 0 },
                    { key: "Review Required", label: "Review Required", count: statusCounts["Review Required"] || 0 },
                    { key: "Failed", label: "Failed", count: statusCounts.Failed || 0 },
                  ].map((status) => (
                    <button
                      key={status.key}
                      onClick={() => setSelectedStatus(status.key)}
                      className={`w-full flex items-center justify-between p-3 rounded-lg text-left transition-colors ${
                        selectedStatus === status.key
                          ? "bg-purple-50 border-2 border-purple-200 text-purple-700"
                          : "bg-gray-50 hover:bg-gray-100 border-2 border-transparent"
                      }`}
                    >
                      <span className="font-medium">{status.label}</span>
                      <Badge variant="secondary" className="bg-white">
                        {status.count}
                      </Badge>
                    </button>
                  ))}
                </div>
              </div>

              {/* Bank Filter */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-700">Bank</label>
                <Select value={selectedBank} onValueChange={setSelectedBank}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Banks" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Banks</SelectItem>
                    {uniqueBanks.map((bank) => (
                      <SelectItem key={bank} value={bank}>
                        {bank}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              {/* Quick Actions */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Quick Actions</label>
                <div className="space-y-2">
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <Download className="h-4 w-4 mr-2" />
                    Export All
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <Star className="h-4 w-4 mr-2" />
                    Favorites
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: File List */}
        <div className="flex-1">
          <div className="space-y-4">
            {filteredFiles.length === 0 ? (
              <Card className="shadow-lg border-0">
                <CardContent className="p-12 text-center">
                  <div className="flex flex-col items-center gap-4">
                    <div className="p-6 bg-gray-100 rounded-full">
                      <FolderOpen className="h-16 w-16 text-gray-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">No files found</h3>
                      <p className="text-gray-600 mb-6">
                        {searchQuery || selectedStatus !== "all" || selectedBank !== "all"
                          ? "Try adjusting your filters"
                          : "Upload your first bank statement to get started"}
                      </p>
                      <Button
                        onClick={() => setIsUploadDialogOpen(true)}
                        className="bg-gradient-to-r from-purple-600 to-blue-600"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Statement
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              filteredFiles.map((file) => (
                <Card key={file.id} className="shadow-lg border-0 hover:shadow-xl transition-all duration-300 group">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-6">
                      {/* File Icon & Color */}
                      <div className="flex-shrink-0">
                        <div
                          className={`w-16 h-16 ${file.color} rounded-2xl flex items-center justify-center shadow-lg`}
                        >
                          <FileText className="h-8 w-8 text-white" />
                        </div>
                      </div>

                      {/* File Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="text-xl font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">
                              {file.name}
                            </h3>
                            <p className="text-gray-600 mt-1">{file.bankName}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(file.status)}
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Download className="h-4 w-4 mr-2" />
                                  Download
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <Star className="h-4 w-4 mr-2" />
                                  Add to Favorites
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </div>

                        {/* File Metadata */}
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Date Range</p>
                            <p className="text-sm font-medium text-gray-900">{file.dateRange}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Entries</p>
                            <p className="text-sm font-medium text-gray-900">{file.entries}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">File Size</p>
                            <p className="text-sm font-medium text-gray-900">{file.fileSize}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Uploaded</p>
                            <p className="text-sm font-medium text-gray-900">{formatDate(file.uploadDate)}</p>
                          </div>
                        </div>

                        {/* Progress Bar (for processing files) */}
                        {file.status === "Processing" && (
                          <div className="mb-4">
                            <div className="flex justify-between text-sm mb-2">
                              <span className="text-gray-600">Processing Progress</span>
                              <span className="font-medium text-blue-600">{file.processingProgress}%</span>
                            </div>
                            <Progress value={file.processingProgress} className="h-2" />
                          </div>
                        )}

                        {/* Status & Actions */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <Badge
                              variant="outline"
                              className={`${
                                file.status === "Completed"
                                  ? "border-green-200 bg-green-50 text-green-700"
                                  : file.status === "Processing"
                                    ? "border-blue-200 bg-blue-50 text-blue-700"
                                    : file.status === "Review Required"
                                      ? "border-orange-200 bg-orange-50 text-orange-700"
                                      : "border-red-200 bg-red-50 text-red-700"
                              }`}
                            >
                              {file.status}
                            </Badge>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Users className="h-4 w-4" />
                              <span>{file.uploadedBy}</span>
                            </div>
                          </div>
                          <Button
                            onClick={() => onReviewFile(file)}
                            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            Review File
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Upload Dialog */}
      <UploadBankStatementDialog
        open={isUploadDialogOpen}
        onOpenChange={setIsUploadDialogOpen}
        onUpload={handleUpload}
      />
    </div>
  )
}
