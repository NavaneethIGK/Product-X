/**
 * CSV Data Loader - Fetches and parses shipment data
 */

export interface ShipmentRecord {
  shipment_id: string
  source_location: string
  destination_location: string
  departed_at: string
  expected_arrival: string
  arrived_at: string
  status: string
  sku: string
  quantity: number
}

export interface DashboardMetrics {
  totalShipments: number
  arrivedCount: number
  inTransitCount: number
  delayedCount: number
  onTimePercentage: number
  delayPercentage: number
  averageDelayDays: number
  routeMetrics: Record<string, { count: number; delayRate: number }>
  skuMetrics: Record<string, { count: number; delayRate: number }>
}

// Parse CSV text to records
function parseCSV(text: string): ShipmentRecord[] {
  const lines = text.trim().split('\n')
  if (lines.length < 2) return []

  const headers = lines[0].split(',').map((h) => h.trim())
  const records: ShipmentRecord[] = []

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map((v) => v.trim())
    if (values.length !== headers.length) continue

    records.push({
      shipment_id: values[0],
      source_location: values[1],
      destination_location: values[2],
      departed_at: values[3],
      expected_arrival: values[4],
      arrived_at: values[5],
      status: values[6],
      sku: values[7],
      quantity: parseInt(values[8]) || 0
    })
  }

  return records
}

// Calculate if shipment is delayed
function isDelayed(
  expectedArrival: string,
  arrivedAt: string,
  status: string
): boolean {
  if (status === 'in_transit') return false
  if (!arrivedAt) return false

  try {
    const expected = new Date(expectedArrival).getTime()
    const actual = new Date(arrivedAt).getTime()
    return actual > expected
  } catch {
    return false
  }
}

// Calculate delay in days
function calculateDelayDays(expectedArrival: string, arrivedAt: string): number {
  if (!arrivedAt) return 0

  try {
    const expected = new Date(expectedArrival).getTime()
    const actual = new Date(arrivedAt).getTime()
    const diffMs = actual - expected
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
    return Math.max(0, diffDays)
  } catch {
    return 0
  }
}

// Analyze shipment data and calculate metrics
export function analyzeShipments(records: ShipmentRecord[]): DashboardMetrics {
  const totalShipments = records.length
  let arrivedCount = 0
  let inTransitCount = 0
  let delayedCount = 0
  let totalDelayDays = 0
  const routeMetrics: Record<string, { count: number; delayed: number }> = {}
  const skuMetrics: Record<string, { count: number; delayed: number }> = {}

  records.forEach((record) => {
    if (record.status === 'arrived') {
      arrivedCount++

      const delayed = isDelayed(record.expected_arrival, record.arrived_at, record.status)
      if (delayed) {
        delayedCount++
        totalDelayDays += calculateDelayDays(record.expected_arrival, record.arrived_at)
      }
    } else if (record.status === 'in_transit') {
      inTransitCount++
    }

    // Route metrics
    const route = `${record.source_location}->${record.destination_location}`
    if (!routeMetrics[route]) {
      routeMetrics[route] = { count: 0, delayed: 0 }
    }
    routeMetrics[route].count++
    if (
      record.status === 'arrived' &&
      isDelayed(record.expected_arrival, record.arrived_at, record.status)
    ) {
      routeMetrics[route].delayed++
    }

    // SKU metrics
    if (!skuMetrics[record.sku]) {
      skuMetrics[record.sku] = { count: 0, delayed: 0 }
    }
    skuMetrics[record.sku].count++
    if (
      record.status === 'arrived' &&
      isDelayed(record.expected_arrival, record.arrived_at, record.status)
    ) {
      skuMetrics[record.sku].delayed++
    }
  })

  const onTimePercentage = arrivedCount > 0 ? ((arrivedCount - delayedCount) / arrivedCount) * 100 : 0
  const delayPercentage = 100 - onTimePercentage
  const averageDelayDays = delayedCount > 0 ? totalDelayDays / delayedCount : 0

  // Convert to percentages
  const convertedRouteMetrics: Record<string, { count: number; delayRate: number }> = {}
  Object.entries(routeMetrics).forEach(([route, { count, delayed }]) => {
    convertedRouteMetrics[route] = {
      count,
      delayRate: count > 0 ? (delayed / count) * 100 : 0
    }
  })

  const convertedSkuMetrics: Record<string, { count: number; delayRate: number }> = {}
  Object.entries(skuMetrics).forEach(([sku, { count, delayed }]) => {
    convertedSkuMetrics[sku] = {
      count,
      delayRate: count > 0 ? (delayed / count) * 100 : 0
    }
  })

  return {
    totalShipments,
    arrivedCount,
    inTransitCount,
    delayedCount,
    onTimePercentage: Math.round(onTimePercentage * 100) / 100,
    delayPercentage: Math.round(delayPercentage * 100) / 100,
    averageDelayDays: Math.round(averageDelayDays * 100) / 100,
    routeMetrics: convertedRouteMetrics,
    skuMetrics: convertedSkuMetrics
  }
}

// Fetch CSV from local file or server
export async function fetchAndAnalyzeCSV(filePath: string = '/shipment_data_1M.csv'): Promise<DashboardMetrics> {
  try {
    const response = await fetch(filePath)
    const text = await response.text()
    const records = parseCSV(text)
    return analyzeShipments(records)
  } catch (error) {
    console.error('Error loading CSV:', error)
    // Return fallback metrics
    return {
      totalShipments: 0,
      arrivedCount: 0,
      inTransitCount: 0,
      delayedCount: 0,
      onTimePercentage: 0,
      delayPercentage: 0,
      averageDelayDays: 0,
      routeMetrics: {},
      skuMetrics: {}
    }
  }
}
