"use client"

import { useState } from "react"
import { supabase } from "@/lib/supabaseClient"

import {
  LayoutDashboard,
  CreditCard,
  ShoppingCart,
  Receipt,
  FileText,
  Upload,
  Search,
  Bell,
  User,
  CheckCircle,
  Clock,
  TrendingUp,
  Download,
  Eye,
  Bot,
  LogOut,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Separator } from "@/components/ui/separator"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import LoginForm  from "./login"
import SignupForm from "./signup-form"
import { BankingEntriesPage } from "./banking-entries-page"
import {BankingFilesPage} from "./banking-files"
const sidebarItems = [

  { title: "Dashboard", icon: LayoutDashboard, id: "dashboard" },
  { title: "Banking Entries", icon: CreditCard, id: "banking" },
  { title: "Banking Statements", icon: CreditCard, id: "statements" },


]

const mockFiles = [
  {
    id: 1,
    name: "bank_statement_march_2024.pdf",
    uploadDate: "2024-03-15 14:30",
    uploadedBy: "John Doe",
    bankLedger: "HDFC Bank",
    dateRange: "01-03-2024 - 31-03-2024",
    status: "In Review",
    entries: 45,
    resolved: 42,
    pending: 3,
  },
  {
    id: 2,
    name: "purchase_invoices_feb_2024.xlsx",
    uploadDate: "2024-02-28 16:45",
    uploadedBy: "Jane Smith",
    bankLedger: "ICICI Bank",
    dateRange: "01-02-2024 - 28-02-2024",
    status: "Processed",
    entries: 78,
    resolved: 78,
    pending: 0,
  },
  {
    id: 3,
    name: "sales_data_jan_2024.csv",
    uploadDate: "2024-01-31 11:20",
    uploadedBy: "Mike Johnson",
    bankLedger: "SBI Bank",
    dateRange: "01-01-2024 - 31-01-2024",
    status: "Issue Fixed",
    entries: 156,
    resolved: 150,
    pending: 6,
  },
]

export function GridAIDashboard() {
  const [activeSection, setActiveSection] = useState("dashboard")
  const [selectedFile, setSelectedFile] = useState<any>(null)




 
const handleLogout = async () => {
  await supabase.auth.signOut()
}


  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">GRID AI Dashboard</h1>
          <p className="text-muted-foreground">AI-powered Tally ERP management</p>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
          <Button size="sm">
            <Upload className="h-4 w-4 mr-2" />
            Upload Files
          </Button>
        </div>
      </div>

      {/* AI Insights Banner */}
      <Card className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Bot className="h-12 w-12" />
              <div>
                <h3 className="text-xl font-bold">AI Processing Active</h3>
                <p className="opacity-90">Smart entry categorization and error detection enabled</p>
              </div>
            </div>
            <Button variant="secondary" size="sm">
              View Insights
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Entries</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+12%</span> from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,156</div>
            <p className="text-xs text-muted-foreground">93.7% completion rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Clock className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">78</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Accuracy</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">96.2%</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+2.1%</span> improvement
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest file uploads and processing status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockFiles.slice(0, 3).map((file) => (
              <div key={file.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <FileText className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {file.entries} entries • {file.uploadDate}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      file.status === "Processed" ? "default" : file.status === "In Review" ? "secondary" : "outline"
                    }
                  >
                    {file.status}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderContent = () => {
    switch (activeSection) {
      case "dashboard":
        return renderDashboard()
      case "banking":
        return <BankingEntriesPage />
      case "purchase":
        return (
          <div className="space-y-6">
            <h1 className="text-3xl font-bold">Purchase Entries</h1>
            <Card>
              <CardContent className="p-8 text-center">
                <ShoppingCart className="h-12 w-12 mx-auto text-mu ted-foreground mb-4" />
                <p className="text-muted-foreground">Purchase entries management coming soon...</p>
              </CardContent>
            </Card>
          </div>
        )
        case "statements":
        return <BankingFilesPage onReviewFile={file => console.log(file)} />

     
      case "sales":
        return (
          <div className="space-y-6">
            <h1 className="text-3xl font-bold">Sales Entries</h1>
            <Card>
              <CardContent className="p-8 text-center">
                <Receipt className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Sales entries management coming soon...</p>
              </CardContent>
            </Card>
          </div>
        )
      default:
        return renderDashboard()
    }
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <Sidebar>
          <SidebarHeader className="p-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-lg">GRID AI</h2>
                <p className="text-xs text-muted-foreground">Tally ERP Manager</p>
              </div>
            </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Navigation</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {sidebarItems.map((item) => (
                    <SidebarMenuItem key={item.id}>
                      <SidebarMenuButton onClick={() => setActiveSection(item.id)} isActive={activeSection === item.id}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Connectivity Status</SidebarGroupLabel>
              <SidebarGroupContent>
                <div className="space-y-3 px-2">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="text-sm font-medium">Tally Connector</p>
                        <p className="text-xs text-muted-foreground">Connected</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="text-sm font-medium">Tally Software</p>
                        <p className="text-xs text-muted-foreground">Port: 9000</p>
                      </div>
                    </div>
                  </div>
                </div>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter className="p-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div className="flex items-center gap-2 p-2 rounded-lg bg-muted cursor-pointer hover:bg-muted/80">
                  <User className="h-4 w-4" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">John Doe</p>
                    <p className="text-xs text-muted-foreground truncate">Admin</p>
                  </div>
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem>
                  <User className="h-4 w-4 mr-2" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarFooter>
        </Sidebar>
        <SidebarInset className="flex-1">
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <div className="flex items-center gap-2 flex-1">
          
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm">
                <Bell className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <User className="h-4 w-4" />
              </Button>
            </div>
          </header>
          <main className="flex-1 overflow-auto p-6">{renderContent()}</main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
