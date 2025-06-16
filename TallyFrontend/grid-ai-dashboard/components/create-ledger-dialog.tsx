"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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

interface CreateLedgerDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreateLedger: (ledger: any) => void
}

export function CreateLedgerDialog({ open, onOpenChange, onCreateLedger }: CreateLedgerDialogProps) {
  const [name, setName] = useState("")
  const [parentGroup, setParentGroup] = useState("")
  const [gstin, setGstin] = useState("")
  const [stateCode, setStateCode] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const parentGroups = [
    "Bank Accounts",
    "Cash-in-Hand",
    "Current Assets",
    "Current Liabilities",
    "Expenses (Direct)",
    "Expenses (Indirect)",
    "Fixed Assets",
    "Income (Direct)",
    "Income (Indirect)",
    "Investments",
    "Loans & Advances (Asset)",
    "Loans (Liability)",
    "Misc. Expenses (Asset)",
    "Suspense Account",
  ]

  const stateCodes = [
    { code: "01", name: "Jammu & Kashmir" },
    { code: "02", name: "Himachal Pradesh" },
    { code: "03", name: "Punjab" },
    { code: "04", name: "Chandigarh" },
    { code: "05", name: "Uttarakhand" },
    { code: "06", name: "Haryana" },
    { code: "07", name: "Delhi" },
    { code: "08", name: "Rajasthan" },
    { code: "09", name: "Uttar Pradesh" },
    { code: "10", name: "Bihar" },
    { code: "11", name: "Sikkim" },
    { code: "12", name: "Arunachal Pradesh" },
    { code: "13", name: "Nagaland" },
    { code: "14", name: "Manipur" },
    { code: "15", name: "Mizoram" },
    { code: "16", name: "Tripura" },
    { code: "17", name: "Meghalaya" },
    { code: "18", name: "Assam" },
    { code: "19", name: "West Bengal" },
    { code: "20", name: "Jharkhand" },
    { code: "21", name: "Odisha" },
    { code: "22", name: "Chhattisgarh" },
    { code: "23", name: "Madhya Pradesh" },
    { code: "24", name: "Gujarat" },
    { code: "26", name: "Dadra & Nagar Haveli and Daman & Diu" },
    { code: "27", name: "Maharashtra" },
    { code: "29", name: "Karnataka" },
    { code: "30", name: "Goa" },
    { code: "31", name: "Lakshadweep" },
    { code: "32", name: "Kerala" },
    { code: "33", name: "Tamil Nadu" },
    { code: "34", name: "Puducherry" },
    { code: "35", name: "Andaman & Nicobar Islands" },
    { code: "36", name: "Telangana" },
    { code: "37", name: "Andhra Pradesh" },
    { code: "38", name: "Ladakh" },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 800))

    const newLedger = {
      id: `ledger-${Date.now()}`,
      name,
      parentGroup,
      gstin,
      stateCode,
    }

    onCreateLedger(newLedger)
    setIsSubmitting(false)
    resetForm()
    onOpenChange(false)
  }

  const resetForm = () => {
    setName("")
    setParentGroup("")
    setGstin("")
    setStateCode("")
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">Create Ledger</DialogTitle>
          <DialogDescription>Create a new ledger account to categorize your transactions.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name" className="font-medium">
                Name<span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                placeholder="Ledger Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="parentGroup" className="font-medium">
                Parent Group<span className="text-red-500">*</span>
              </Label>
              <Select value={parentGroup} onValueChange={setParentGroup} required>
                <SelectTrigger id="parentGroup">
                  <SelectValue placeholder="Select Parent Group" />
                </SelectTrigger>
                <SelectContent>
                  {parentGroups.map((group) => (
                    <SelectItem key={group} value={group}>
                      {group}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="gstin" className="font-medium">
                GSTIN
              </Label>
              <Input id="gstin" placeholder="GSTN" value={gstin} onChange={(e) => setGstin(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="stateCode" className="font-medium">
                State Code
              </Label>
              <Select value={stateCode} onValueChange={setStateCode}>
                <SelectTrigger id="stateCode">
                  <SelectValue placeholder="State Code" />
                </SelectTrigger>
                <SelectContent>
                  {stateCodes.map((state) => (
                    <SelectItem key={state.code} value={state.code}>
                      {state.code} - {state.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" className="bg-purple-600 hover:bg-purple-700" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Ledger"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
