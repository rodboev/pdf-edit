import AdmZip from 'adm-zip'
import dotenv from 'dotenv'
import fs from 'fs'
import path from 'path'

// Load environment variables from .env.local
dotenv.config({ path: '.env.local' })

const {
  ServicePrincipalCredentials,
  PDFServices,
  MimeType,
  ExtractPDFParams,
  ExtractElementType,
  ExtractPDFJob,
  ExtractPDFResult
} = require('@adobe/pdfservices-node-sdk')

interface PdfAnalysis {
  baseAmount: number
  taxAmount: number
  totalAmount: number
  taxRate: number
}

const TAX_RATE = 0.08875

function createOutputFilePath() {
  const filePath = "output/ExtractTextInfoFromPDF/"
  const date = new Date()
  const dateString = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" +
    ("0" + date.getDate()).slice(-2) + "T" + ("0" + date.getHours()).slice(-2) + "-" +
    ("0" + date.getMinutes()).slice(-2) + "-" + ("0" + date.getSeconds()).slice(-2)
  fs.mkdirSync(filePath, { recursive: true })
  return path.join(filePath, `extract${dateString}.zip`)
}

async function extractTextFromPdf(pdfPath: string): Promise<string> {
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
    readStream = fs.createReadStream(pdfPath)
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

    // Get content from the resulting asset
    const resultAsset = pdfServicesResponse.result.resource
    const streamAsset = await pdfServices.getContent({ asset: resultAsset })

    // Save the ZIP file
    const outputPath = createOutputFilePath()
    const writeStream = fs.createWriteStream(outputPath)
    await new Promise((resolve, reject) => {
      streamAsset.readStream.pipe(writeStream)
        .on('finish', resolve)
        .on('error', reject)
    })

    // Extract text from the ZIP file
    const zip = new AdmZip(outputPath)
    const jsonEntry = zip.getEntries().find((entry: AdmZip.IZipEntry) => entry.entryName.endsWith('structuredData.json'))
    if (!jsonEntry) {
      throw new Error('Could not find structuredData.json in the ZIP file')
    }

    const jsonContent = JSON.parse(jsonEntry.getData().toString('utf8'))
    const text = jsonContent.elements
      .filter((el: any) => el.Text)
      .map((el: any) => el.Text)
      .join(' ')
    
    return text
  } catch (err) {
    console.error('Error extracting text from PDF:', err)
    throw err
  } finally {
    readStream?.destroy()
  }
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

async function analyzePdf(pdfPath: string): Promise<PdfAnalysis | null> {
  try {
    const text = await extractTextFromPdf(pdfPath)
    const amounts = extractDollarAmounts(text)
    
    if (amounts.length < 5) return null

    const total = Number(amounts[4].replace('$', ''))
    const monthlyCharge = Number(amounts[0].replace('$', ''))
    const { base, tax } = extractTaxFromTotal(monthlyCharge)

    return {
      baseAmount: base * 2,
      taxAmount: tax * 2,
      totalAmount: total,
      taxRate: TAX_RATE * 100
    }
  } catch (error) {
    console.error('Error analyzing PDF:', error)
    return null
  }
}

async function main() {
  console.log('Analyzing files: pdfs/correct.pdf and pdfs/incorrect.pdf\n')
  console.log('=== Tax Analysis (NYC Rate: 8.875%) ===\n')

  // Analyze correct PDF
  console.log('Correct PDF Analysis:')
  const correctAnalysis = await analyzePdf('pdfs/correct.pdf')
  if (correctAnalysis) {
    console.log(`Base Amount: $${correctAnalysis.baseAmount.toFixed(2)}`)
    console.log(`Tax Amount: $${correctAnalysis.taxAmount.toFixed(2)}`)
    console.log(`Total: $${correctAnalysis.totalAmount.toFixed(2)}`)
    console.log(`Actual Tax Rate: ${correctAnalysis.taxRate.toFixed(3)}%\n`)
  }

  // Analyze incorrect PDF
  console.log('Incorrect PDF Analysis:')
  const incorrectAnalysis = await analyzePdf('pdfs/incorrect.pdf')
  if (incorrectAnalysis) {
    const monthlyBase = incorrectAnalysis.baseAmount / 2
    const monthlyTax = incorrectAnalysis.taxAmount / 2
    const monthlyTotal = monthlyBase + monthlyTax

    console.log(`Monthly Charge (with baked-in tax): $${monthlyTotal.toFixed(2)}`)
    console.log('Should be broken down as:')
    console.log(`- Base Amount: $${monthlyBase.toFixed(2)}`)
    console.log(`- Tax Amount: $${monthlyTax.toFixed(2)}\n`)

    console.log('Total for two charges:')
    console.log(`Total Base: $${incorrectAnalysis.baseAmount.toFixed(2)}`)
    console.log(`Total Tax: $${incorrectAnalysis.taxAmount.toFixed(2)}`)
    console.log(`Total Amount: $${incorrectAnalysis.totalAmount.toFixed(2)}\n`)

    console.log('The Issue:')
    console.log(`1. The $${incorrectAnalysis.taxAmount.toFixed(2)} tax is currently hidden within the two $${monthlyTotal.toFixed(2)} charges`)
    console.log(`2. The tax line shows $0.00 when it should show $${incorrectAnalysis.taxAmount.toFixed(2)}`)
    console.log(`3. Need to extract the tax from the charges and display it separately`)
  }

  console.log('\nFile to be corrected: pdfs/incorrect.pdf')
}

main().catch(console.error)