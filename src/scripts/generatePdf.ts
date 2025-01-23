import dotenv from 'dotenv'
import fs from 'fs'
import path from 'path'

// Load environment variables from .env.local
dotenv.config({ path: path.join(process.cwd(), '.env.local') })

const {
  ServicePrincipalCredentials,
  ExecutionContext,
  DocumentMerge,
  FileRef
} = require('@adobe/pdfservices-node-sdk')

interface InvoiceData {
  customerInfo: {
    name: string
    address: string
    city: string
    state: string
    zip: string
  }
  invoiceInfo: {
    number: string
    date: string
    poNumber: string
    terms: string
  }
  services: Array<{
    description: string
    quantity: number
    price: number
  }>
  totals: {
    subtotal: number
    tax: number
    total: number
  }
}

function createDateString() {
  const date = new Date()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const year = date.getFullYear() % 100
  return `${month}-${day}-${year}`
}

async function generatePDF() {
  try {
    const rootDir = process.cwd()
    
    // Initial setup, create credentials instance
    const credentials = new ServicePrincipalCredentials({
      clientId: process.env.ADOBE_API_KEY,
      clientSecret: process.env.ADOBE_CLIENT_SECRET
    })

    // Create an ExecutionContext using credentials
    const executionContext = ExecutionContext.create(credentials)

    // Read the JSON data
    const dateString = createDateString()
    const jsonPath = path.join(rootDir, "docs", "json", `text-${dateString}.json`)
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'))

    // Transform the JSON data into the format expected by the template
    const jsonDataForMerge = {
      customerInfo: {
        name: "Prime Produce Community Center",
        address: "424 W 54th St",
        city: "New York",
        state: "NY",
        zip: "10019-4406"
      },
      invoiceInfo: {
        number: "1148151",
        date: "01/10/2025",
        poNumber: "",
        terms: "NET 30"
      },
      services: [
        {
          description: "MONTHLY COST",
          quantity: 1,
          price: 200.00
        },
        {
          description: "NEW ACCOUNT EQUIPMENT OR SPECIAL SERVICE",
          quantity: 1,
          price: 200.00
        }
      ],
      totals: {
        subtotal: 400.00,
        tax: 35.50,
        total: 435.50
      }
    }

    // Create a new DocumentMerge options instance
    const documentMerge = DocumentMerge,
      documentMergeOptions = documentMerge.options,
      options = new documentMergeOptions.DocumentMergeOptions(jsonDataForMerge, documentMergeOptions.OutputFormat.PDF)

    // Create a new operation instance using the options instance
    const documentMergeOperation = documentMerge.Operation.createNew(options)

    // Set operation input document template from a source file
    const templatePath = path.join(rootDir, "docs", "template", "template.docx")
    const input = FileRef.createFromLocalFile(templatePath)
    documentMergeOperation.setInput(input)

    // Create output directory if it doesn't exist
    const outputDir = path.join(rootDir, "output")
    fs.mkdirSync(outputDir, { recursive: true })

    // Execute the operation and Save the result to the specified location
    const outputPath = path.join(outputDir, `invoice-${dateString}.pdf`)
    await documentMergeOperation.execute(executionContext)
      .then((result: { saveAsFile: (path: string) => void }) => result.saveAsFile(outputPath))

    console.log(`Successfully generated PDF: ${outputPath}`)
  } catch (err) {
    console.error('Exception encountered while executing operation', err)
    throw err
  }
}

async function main() {
  // Ensure output directory exists
  const rootDir = process.cwd()
  fs.mkdirSync(path.join(rootDir, 'output'), { recursive: true })
  fs.mkdirSync(path.join(rootDir, 'resources'), { recursive: true })

  console.log('Generating new PDF from template and JSON data...')
  await generatePDF()
}

main().catch(console.error) 