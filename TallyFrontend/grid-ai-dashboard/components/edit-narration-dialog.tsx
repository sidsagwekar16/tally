"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface EditNarrationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  narration: string
  remark: string
  onSave: (narration: string, remark: string) => void
}

export function EditNarrationDialog({ open, onOpenChange, narration, remark, onSave }: EditNarrationDialogProps) {
  const [editedNarration, setEditedNarration] = useState(narration)
  const [editedRemark, setEditedRemark] = useState(remark || "")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 500))

    onSave(editedNarration, editedRemark)
    setIsSubmitting(false)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Edit Transaction Details</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="narration" className="font-medium">
                Edit Narration:
              </Label>
              <Textarea
                id="narration"
                value={editedNarration}
                onChange={(e) => setEditedNarration(e.target.value)}
                className="min-h-[80px]"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="remark" className="font-medium">
                Add Remark:
              </Label>
              <Textarea
                id="remark"
                placeholder="Add remark"
                value={editedRemark}
                onChange={(e) => setEditedRemark(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
