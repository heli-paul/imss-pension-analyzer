"use client"
import * as React from "react"
import { cn } from "@/lib/utils"

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => {
    return (
      <label
        className={cn("text-sm font-medium", className)}
        ref={ref}
        {...props}
      />
    )
  }
)
Label.displayName = "Label"
export { Label }
