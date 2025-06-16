"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Upload, FileText, X } from "lucide-react"
import { format } from "date-fns"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

interface UploadBankStatementDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpload: (fileData: any) => void
}

export function UploadBankStatementDialog({ open, onOpenChange, onUpload }: UploadBankStatementDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [bankLedger, setBankLedger] = useState("")
  const [bankName, setBankName] = useState("")
  const [startDate, setStartDate] = useState<Date | undefined>(undefined)
  const [endDate, setEndDate] = useState<Date | undefined>(undefined)
  const [isPasswordProtected, setIsPasswordProtected] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const bankLedgers = [
    "HDFC Bank Current Account",
    "ICICI Bank Savings Account",
    "SBI Bank Current Account",
    "Axis Bank Savings Account",
    "Kotak Mahindra Bank",
    "Yes Bank Current Account",
    "Punjab National Bank",
    "Bank of Baroda",
    "Canara Bank",
    "Union Bank of India",
  ]

  const bankNames = [
    "HDFC Bank",
    "ICICI Bank",
    "State Bank of India (SBI)",
    "Axis Bank",
    "Kotak Mahindra Bank",
    "Yes Bank",
    "Punjab National Bank",
    "Bank of Baroda",
    "Canara Bank",
    "Union Bank of India",
    "IDFC First Bank",
    "IndusInd Bank",
    "Federal Bank",
    "South Indian Bank",
    "Karur Vysya Bank",
    "City Union Bank",
    "Tamilnad Mercantile Bank",
    "Dhanlaxmi Bank",
    "RBL Bank",
    "Bandhan Bank",
  ]

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
        setSelectedFile(file)
      } else {
        alert("Please upload a PDF file only.")
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
        setSelectedFile(file)
      } else {
        alert("Please upload a PDF file only.")
      }
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedFile || !bankLedger || !bankName) {
      alert("Please fill in all required fields and select a file.")
      return
    }

    setIsUploading(true)

    // Simulate file upload delay
    await new Promise((resolve) => setTimeout(resolve, 2000))

    const uploadData = {
      file: selectedFile,
      bankLedger,
      bankName,
      startDate,
      endDate,
      isPasswordProtected,
      uploadDate: new Date().toISOString(),
    }

    onUpload(uploadData)
    setIsUploading(false)
    resetForm()
    onOpenChange(false)
  }

  const resetForm = () => {
    setSelectedFile(null)
    setBankLedger("")
    setBankName("")
    setStartDate(undefined)
    setEndDate(undefined)
    setIsPasswordProtected(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">Document Details</DialogTitle>
          <DialogDescription>Upload your bank statement for processing</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload Area */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Upload Bank Statement</Label>
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragActive
                  ? "border-purple-500 bg-purple-50"
                  : selectedFile
                    ? "border-green-500 bg-green-50"
                    : "border-gray-300 hover:border-gray-400"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {selectedFile ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-center gap-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <FileText className="h-8 w-8 text-blue-600" />
                    <div className="flex-1 text-left">
                      <p className="font-medium text-blue-900">File Name: {selectedFile.name}</p>
                      <p className="text-sm text-blue-600">Size: {formatFileSize(selectedFile.size)}</p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={removeFile}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="h-12 w-12 mx-auto text-gray-400" />
                  <div>
                    <p className="text-lg font-medium">Drop your bank statement here</p>
                    <p className="text-sm text-gray-500">or click to browse files</p>
                  </div>
                  <Button type="button" variant="outline" onClick={() => fileInputRef.current?.click()}>
                    Choose File
                  </Button>
                </div>
              )}
              <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" />
            </div>
          </div>

          {/* Bank Ledger */}
          <div className="space-y-2">
            <Label htmlFor="bankLedger" className="text-sm font-medium">
              Bank Ledger<span className="text-red-500">*</span>
            </Label>
            <Select value={bankLedger} onValueChange={setBankLedger} required>
              <SelectTrigger>
                <SelectValue placeholder="Select an Option" />
              </SelectTrigger>
              <SelectContent>
                {bankLedgers.map((ledger) => (
                  <SelectItem key={ledger} value={ledger}>
                    {ledger}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Bank Name */}
          <div className="space-y-2">
            <Label htmlFor="bankName" className="text-sm font-medium">
              Bank Name<span className="text-red-500">*</span>
            </Label>
            <Select value={bankName} onValueChange={setBankName} required>
              <SelectTrigger>
                <SelectValue placeholder="Select Bank" />
              </SelectTrigger>
              <SelectContent>
                {bankNames.map((bank) => (
                  <SelectItem key={bank} value={bank}>
                    {bank}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Extraction Period */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Extraction Period [DD-MM-YYYY] (optional)</Label>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start text-left font-normal">
                      {startDate ? format(startDate, "dd-MM-yyyy") : "Start date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar mode="single" selected={startDate} onSelect={setStartDate} initialFocus />
                  </PopoverContent>
                </Popover>
              </div>
              <span className="text-gray-400">→</span>
              <div className="flex-1">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start text-left font-normal">
                      {endDate ? format(endDate, "dd-MM-yyyy") : "End date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar mode="single" selected={endDate} onSelect={setEndDate} initialFocus />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </div>

          {/* Password Protected Checkbox */}
          <div className="flex items-center space-x-2">
            <Checkbox id="passwordProtected" checked={isPasswordProtected} onCheckedChange={setIsPasswordProtected} />
            <Label htmlFor="passwordProtected" className="text-sm">
              File is Password Protected
            </Label>
          </div>

          {/* Important Notes */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-orange-600">* Important notes:</Label>
            <ul className="space-y-1 text-sm text-purple-600">
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>Make sure the PDF contains headers for the transaction table.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>We currently do not support multi account bank statement summary.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>Do not remove the statement password.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>Do not upload merged statements.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>We currently do not support scanned copies or image based bank statements.</span>
              </li>
            </ul>
          </div>

          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isUploading}>
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-purple-600 hover:bg-purple-700"
              disabled={isUploading || !selectedFile || !bankLedger || !bankName}
            >
              {isUploading ? "Uploading..." : "Upload File"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
