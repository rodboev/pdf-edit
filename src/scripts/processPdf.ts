import AdmZip from 'adm-zip'
import dotenv from 'dotenv'
import fs from 'fs'
import path from 'path'

// Load environment variables from .env.local
dotenv.config({ path: '.env.local' })

function createDateString() {
  const date = new Date()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const year = date.getFullYear() % 100
  return `${month}-${day}-${year}`
}

// Global path constants
const rootDir = process.cwd()
const dateString = createDateString()
const templatePath = path.join(rootDir, "src", "docs", "template.docx")
const datedTemplateDataPath = path.join(rootDir, "data", "json", `template-${dateString}.json`)
const outputPath = path.join(rootDir, "output", `invoice-${dateString}.pdf`)

const {
  ServicePrincipalCredentials,
  PDFServices,
  MimeType,
  DocumentMergeParams,
  OutputFormat,
  DocumentMergeJob,
  DocumentMergeResult,
  ExtractPDFParams,
  ExtractElementType,
  ExtractPDFJob,
  ExtractPDFResult
} = require('@adobe/pdfservices-node-sdk')

const TAX_RATE = 0.08875

interface PdfAnalysis {
  baseAmount: number
  taxAmount: number
  totalAmount: number
  taxRate: number
  needsFixing: boolean
}

interface ExtractedData {
  text: string
  jsonContent: string
}

interface LineItem {
  service: string
  price: string
}

interface TemplateData {
  items: LineItem[]
  subtotal: string
  tax: string
  paid: string
}

function extractDollarAmounts(text: string): string[] {
  const dollarRegex = /\$\d+\.?\d*/g
  return text.match(dollarRegex) || []
}

function extractTaxFromTotal(amount: number): { base: number; tax: number } {
  const base = Number((amount / (1 + TAX_RATE)).toFixed(2))
  const tax = Number((amount - base).toFixed(2))
  return { base, tax }
}

async function extractTextFromPdf(pdfPath: string): Promise<ExtractedData> {
  let readStream
  try {
    // Initial setup, create credentials instance
    const credentials = new ServicePrincipalCredentials({
      clientId: process.env.ADOBE_API_KEY,
      clientSecret: process.env.ADOBE_CLIENT_SECRET
    })

    // Creates a PDF Services instance
    const pdfServices = new PDFServices({ credentials })

    // Creates an asset from source file and upload
    const absolutePdfPath = path.isAbsolute(pdfPath) ? pdfPath : path.join(process.cwd(), pdfPath)
    readStream = fs.createReadStream(absolutePdfPath)
    const inputAsset = await pdfServices.upload({
      readStream,
      mimeType: MimeType.PDF
    })

    // Create parameters for the job
    const params = new ExtractPDFParams({
      elementsToExtract: [ExtractElementType.TEXT]
    })

    // Creates a new job instance
    const job = new ExtractPDFJob({ inputAsset, params })

    // Submit the job and get the job result
    const pollingURL = await pdfServices.submit({ job })
    const pdfServicesResponse = await pdfServices.getJobResult({
      pollingURL,
      resultType: ExtractPDFResult
    })

    // Get content stream from the resulting asset
    const resultAsset = pdfServicesResponse.result.resource
    const streamAsset = await pdfServices.getContent({ asset: resultAsset })

    // Create buffer to hold zip data
    const chunks: Buffer[] = []
    await new Promise((resolve, reject) => {
      streamAsset.readStream
        .on('data', (chunk: Buffer) => chunks.push(chunk))
        .on('end', resolve)
        .on('error', reject)
    })
    
    // Process zip data in memory
    const zipBuffer = Buffer.concat(chunks)
    const zip = new AdmZip(zipBuffer)
    const jsonEntry = zip.getEntries().find((entry: AdmZip.IZipEntry) => entry.entryName.endsWith('structuredData.json'))
    if (!jsonEntry) {
      throw new Error('Could not find structuredData.json in the ZIP data')
    }

    // Extract JSON content
    const jsonContent = jsonEntry.getData().toString('utf8')
    const parsedJson = JSON.parse(jsonContent)
    const text = parsedJson.elements
      .filter((el: any) => el.Text)
      .map((el: any) => el.Text)
      .join(' ')
    
    return { text, jsonContent }
  } catch (err) {
    console.error('Error extracting text from PDF:', err)
    throw err
  } finally {
    readStream?.destroy()
  }
}

async function extractLineItems(text: string): Promise<LineItem[]> {
  const lines = text.split('\n')
  const items: LineItem[] = []
  
  // Find the service description section
  let inServiceSection = false
  let currentService = ''
  
  for (const line of lines) {
    // Start capturing after "Service Description"
    if (line.includes('Service Description')) {
      inServiceSection = true
      continue
    }
    
    if (inServiceSection) {
      const dollarMatch = line.match(/\$(\d+\.\d{2})/)
      if (dollarMatch) {
        // Look for "MONTHLY COST" in the line or previous lines
        const serviceMatch = line.match(/MONTHLY COST/)
        if (serviceMatch || currentService.includes('MONTHLY COST')) {
          items.push({
            service: 'MONTHLY COST',
            price: dollarMatch[1]
          })
          
          // If we found both monthly charges, we're done
          if (items.length === 2) {
            break
          }
        }
      } else if (line.trim()) {
        // Accumulate service description lines that don't have dollar amounts
        currentService = line.trim()
      }
    }
  }

  // If we only found one item but the total suggests two, duplicate it
  if (items.length === 1) {
    items.push({ ...items[0] })
  }

  return items
}

async function analyzePdf(pdfPath: string): Promise<PdfAnalysis | null> {
  try {
    const { text } = await extractTextFromPdf(pdfPath)
    const amounts = extractDollarAmounts(text)
    
    if (amounts.length < 5) {
      console.error('Not enough dollar amounts found in PDF')
      return null
    }

    const total = Number(amounts[4].replace('$', ''))
    const monthlyCharge = Number(amounts[0].replace('$', ''))
    const currentTax = Number(amounts[3].replace('$', ''))
    
    // If tax is already properly separated (tax line shows expected amount),
    // then use the actual values from the PDF
    const needsFixing = Math.abs(currentTax) < 0.01 // Tax line shows $0.00
    
    if (needsFixing) {
      // For incorrect PDFs, extract base amount from total with tax
      const { base, tax } = extractTaxFromTotal(monthlyCharge)
      return {
        baseAmount: base * 2,
        taxAmount: tax * 2,
        totalAmount: total,
        taxRate: TAX_RATE * 100,
        needsFixing: true
      }
    } else {
      // For correct PDFs, use the actual values from the PDF
      return {
        baseAmount: monthlyCharge * 2,
        taxAmount: currentTax,
        totalAmount: total,
        taxRate: (currentTax / (monthlyCharge * 2)) * 100,
        needsFixing: false
      }
    }
  } catch (error) {
    console.error('Error analyzing PDF:', error)
    return null
  }
}

function logAnalysis(name: string, analysis: PdfAnalysis) {
  console.log(`\n${name} Analysis:`)
  const monthlyBase = analysis.baseAmount / 2
  const monthlyTax = analysis.taxAmount / 2

  console.log('Monthly charges:')
  console.log(`- Base Amount: $${monthlyBase.toFixed(2)}`)
  console.log(`- Tax Amount: $${monthlyTax.toFixed(2)}`)
  console.log(`- Monthly Total: $${(monthlyBase + monthlyTax).toFixed(2)}`)

  console.log('\nTotal for two charges:')
  console.log(`- Total Base: $${analysis.baseAmount.toFixed(2)}`)
  console.log(`- Total Tax: $${analysis.taxAmount.toFixed(2)}`)
  console.log(`- Total Amount: $${analysis.totalAmount.toFixed(2)}`)
  console.log(`- Actual Tax Rate: ${analysis.taxRate.toFixed(3)}%`)
}

async function generatePDF(pdfPath: string, analysis: PdfAnalysis) {
  let readStream
  try {
    // Initial setup, create credentials instance
    const credentials = new ServicePrincipalCredentials({
      clientId: process.env.ADOBE_API_KEY,
      clientSecret: process.env.ADOBE_CLIENT_SECRET
    })

    // Creates a PDF Services instance
    const pdfServices = new PDFServices({ credentials })

    // Extract text to get line items
    const { text } = await extractTextFromPdf(pdfPath)
    const lineItems = await extractLineItems(text)

    // Calculate base prices without tax
    const itemsWithoutTax = lineItems.map(item => ({
      service: item.service,
      price: (Number(item.price) / (1 + TAX_RATE)).toFixed(2)
    }))

    // Extract invoice details using regex
    const invoiceMatch = text.match(/Invoice # (\d+)/)
    const dateMatch = text.match(/Date: (\d{2}\/\d{2}\/\d{4})/)
    const timeMatch = text.match(/Time: ([\d:]+\s*[APM]+)/)
    const addressMatch = text.match(/(\d+\s+[^,]+),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)/)

    // Creates an asset from source file and upload
    readStream = fs.createReadStream(templatePath)
    const inputAsset = await pdfServices.upload({
      readStream,
      mimeType: MimeType.DOCX
    })

    // Prepare template data with exact variable names matching the template
    const templateData: TemplateData = {
      items: itemsWithoutTax,
      subtotal: analysis.baseAmount.toFixed(2),
      tax: analysis.taxAmount.toFixed(2),
      paid: analysis.totalAmount.toFixed(2)
    }

    // Save the template data for debugging/reference
    console.log(`\nSaving template data to: ${datedTemplateDataPath}`)
    fs.writeFileSync(datedTemplateDataPath, JSON.stringify(templateData, null, 2))

    // Create parameters for the job
    const params = new DocumentMergeParams({
      jsonDataForMerge: templateData,
      outputFormat: OutputFormat.PDF
    })

    // Creates a new job instance
    const job = new DocumentMergeJob({ inputAsset, params })

    // Submit the job and get the job result
    const pollingURL = await pdfServices.submit({ job })
    const pdfServicesResponse = await pdfServices.getJobResult({
      pollingURL,
      resultType: DocumentMergeResult
    })

    // Get content from the resulting asset
    const resultAsset = pdfServicesResponse.result.asset
    const streamAsset = await pdfServices.getContent({ asset: resultAsset })

    // Create output directory if it doesn't exist
    fs.mkdirSync(path.dirname(outputPath), { recursive: true })

    // Save the result to file
    console.log(`\nSaving ${path.basename(pdfPath)} to ${outputPath}`)
    
    const writeStream = fs.createWriteStream(outputPath)
    await new Promise((resolve, reject) => {
      streamAsset.readStream
        .pipe(writeStream)
        .on('finish', resolve)
        .on('error', reject)
    })

    if (analysis.needsFixing) {
      console.log('\nChanges made:')
      for (let i = 0; i < itemsWithoutTax.length; i++) {
        const original = lineItems[i]
        const fixed = itemsWithoutTax[i]
        console.log(`- Line item "${fixed.service}": $${original.price} → $${fixed.price}`)
      }
      console.log(`- Updated subtotal to $${analysis.baseAmount.toFixed(2)}`)
      console.log(`- Added sales tax line of $${analysis.taxAmount.toFixed(2)}`)
      console.log(`- Total remains $${analysis.totalAmount.toFixed(2)}`)
    } else {
      console.log('\nNo changes needed - tax is already properly separated')
    }
  } catch (err) {
    console.error('Exception encountered while executing operation', err)
    throw err
  } finally {
    readStream?.destroy()
  }
}

async function main() {
  console.log('\n=== PDF Invoice Analysis & Processing ===')
  console.log('\nInput Files:')
  console.log(`Template: ${templatePath}`)
  console.log(`Output Directory: ${path.dirname(outputPath)}`)
  console.log(`\nTax Rate: ${TAX_RATE * 100}%`)

  // Process both PDFs
  const pdfs = [
    { path: 'src/docs/invoice-ok.pdf', name: 'Correct Invoice' },
    { path: 'src/docs/invoice-err.pdf', name: 'Incorrect Invoice' }
  ]

  for (const pdf of pdfs) {
    console.log(`\n=== Processing ${pdf.name} ===`)
    console.log(`File: ${pdf.path}`)
    
    const analysis = await analyzePdf(pdf.path)
    if (!analysis) {
      console.log('Error analyzing PDF - skipping')
      continue
    }

    logAnalysis(pdf.name, analysis)
    
    if (analysis.needsFixing) {
      console.log('\nIssues Found:')
      console.log(`1. Tax ($${analysis.taxAmount.toFixed(2)}) is hidden within the line items`)
      console.log(`2. Each line item includes ${TAX_RATE * 100}% tax`)
      console.log(`3. Tax line shows $0.00 instead of $${analysis.taxAmount.toFixed(2)}`)
      
      console.log('\nGenerating corrected version...')
      await generatePDF(pdf.path, analysis)
    } else {
      console.log('\nNo issues found - tax is properly separated')
    }
  }

  console.log('\nProcessing complete!')
}

main().catch(console.error) 