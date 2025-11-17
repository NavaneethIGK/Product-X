// Sample data structure for the dashboard
export type DashboardMetrics = {
  stockoutRate: number
  returnRate: number
  backorderRate: number
  inventoryTurnover: number
  onTimeDelivery: number
  avgEta: number
  delayedShipments: number
  inTransit: number
}

export type InventoryData = {
  outOfStock: number
  inStock: number
  returnedUnits: number
  orderedUnits: number
  backorders: number
  totalOrders: number
  warehouseStats: Array<{
    warehouse: string
    items: string
    value: string
    turnover: string
    days: string
  }>
}

export type ShipmentData = {
  totalShipments: number
  delivered: number
  inTransit: number
  delayed: number
  shipments: Array<{
    shipmentId: string
    supplier: string
    destination: string
    eta: string
    status: string
    progress: string
  }>
}

export type ETAData = {
  onTimeDelivery: number
  avgEta: number
  delayedShipments: number
  inTransit: number
  etaForecast: Array<{
    date: string
    arrivals: number
  }>
  activeShipments: Array<{
    shipmentId: string
    supplier: string
    destination: string
    eta: string
    status: string
    progress: string
  }>
}

const DASHBOARD_STORAGE_KEY = 'dashboard_metrics'
const INVENTORY_STORAGE_KEY = 'inventory_data'
const SHIPMENT_STORAGE_KEY = 'shipment_data'
const ETA_STORAGE_KEY = 'eta_data'

const defaultDashboardMetrics: DashboardMetrics = {
  stockoutRate: 6.67,
  returnRate: 2.17,
  backorderRate: 1.11,
  inventoryTurnover: 3.76,
  onTimeDelivery: 94.5,
  avgEta: 3.2,
  delayedShipments: 12,
  inTransit: 45
}

const defaultInventoryData: InventoryData = {
  outOfStock: 1,
  inStock: 15,
  returnedUnits: 248,
  orderedUnits: 11434,
  backorders: 1,
  totalOrders: 90,
  warehouseStats: [
    { warehouse: 'Warehouse 1', items: '12,450', value: '$1,245,000', turnover: '3.2x', days: '35 days' },
    { warehouse: 'Warehouse 2', items: '15,230', value: '$1,523,000', turnover: '3.8x', days: '32 days' },
    { warehouse: 'Warehouse 3', items: '10,120', value: '$1,012,000', turnover: '2.9x', days: '40 days' },
    { warehouse: 'Warehouse 4', items: '18,560', value: '$1,856,000', turnover: '4.1x', days: '28 days' },
    { warehouse: 'Warehouse 5', items: '14,890', value: '$1,489,000', turnover: '3.5x', days: '36 days' }
  ]
}

const defaultShipmentData: ShipmentData = {
  totalShipments: 245,
  delivered: 198,
  inTransit: 35,
  delayed: 12,
  shipments: [
    { shipmentId: 'SHP-001', supplier: 'Supplier A', destination: 'New York', eta: '2023-09-25', status: 'On Time', progress: '75%' },
    { shipmentId: 'SHP-002', supplier: 'Supplier B', destination: 'Los Angeles', eta: '2023-09-26', status: 'Delayed', progress: '60%' },
    { shipmentId: 'SHP-003', supplier: 'Supplier C', destination: 'Chicago', eta: '2023-09-24', status: 'On Time', progress: '85%' },
    { shipmentId: 'SHP-004', supplier: 'Supplier D', destination: 'Houston', eta: '2023-09-27', status: 'In Transit', progress: '55%' },
    { shipmentId: 'SHP-005', supplier: 'Supplier A', destination: 'Phoenix', eta: '2023-09-28', status: 'Delayed', progress: '45%' },
    { shipmentId: 'SHP-006', supplier: 'Supplier B', destination: 'Philadelphia', eta: '2023-09-23', status: 'Delivered', progress: '100%' }
  ]
}

const defaultETAData: ETAData = {
  onTimeDelivery: 94.5,
  avgEta: 3.2,
  delayedShipments: 12,
  inTransit: 45,
  etaForecast: [
    { date: 'Sep 20', arrivals: 12 },
    { date: 'Sep 21', arrivals: 8 },
    { date: 'Sep 22', arrivals: 15 },
    { date: 'Sep 23', arrivals: 10 },
    { date: 'Sep 24', arrivals: 18 },
    { date: 'Sep 25', arrivals: 22 },
    { date: 'Sep 26', arrivals: 19 },
    { date: 'Sep 27', arrivals: 25 },
    { date: 'Sep 28', arrivals: 16 },
    { date: 'Sep 29', arrivals: 14 },
    { date: 'Sep 30', arrivals: 11 }
  ],
  activeShipments: [
    { shipmentId: 'SHP-001', supplier: 'Supplier A', destination: 'New York', eta: '2023-09-25', status: 'On Time', progress: '75%' },
    { shipmentId: 'SHP-002', supplier: 'Supplier B', destination: 'Los Angeles', eta: '2023-09-26', status: 'Delayed', progress: '60%' },
    { shipmentId: 'SHP-003', supplier: 'Supplier C', destination: 'Chicago', eta: '2023-09-24', status: 'On Time', progress: '85%' },
    { shipmentId: 'SHP-004', supplier: 'Supplier D', destination: 'Houston', eta: '2023-09-27', status: 'In Transit', progress: '55%' },
    { shipmentId: 'SHP-005', supplier: 'Supplier A', destination: 'Phoenix', eta: '2023-09-28', status: 'Delayed', progress: '45%' },
    { shipmentId: 'SHP-006', supplier: 'Supplier B', destination: 'Philadelphia', eta: '2023-09-23', status: 'Delivered', progress: '100%' }
  ]
}

// Dashboard Metrics
export const getDashboardMetrics = (): DashboardMetrics => {
  const stored = localStorage.getItem(DASHBOARD_STORAGE_KEY)
  return stored ? JSON.parse(stored) : defaultDashboardMetrics
}

export const setDashboardMetrics = (data: DashboardMetrics): void => {
  localStorage.setItem(DASHBOARD_STORAGE_KEY, JSON.stringify(data))
}

export const resetDashboardMetrics = (): void => {
  localStorage.removeItem(DASHBOARD_STORAGE_KEY)
}

// Inventory Data
export const getInventoryData = (): InventoryData => {
  const stored = localStorage.getItem(INVENTORY_STORAGE_KEY)
  return stored ? JSON.parse(stored) : defaultInventoryData
}

export const setInventoryData = (data: InventoryData): void => {
  localStorage.setItem(INVENTORY_STORAGE_KEY, JSON.stringify(data))
}

export const resetInventoryData = (): void => {
  localStorage.removeItem(INVENTORY_STORAGE_KEY)
}

// Shipment Data
export const getShipmentData = (): ShipmentData => {
  const stored = localStorage.getItem(SHIPMENT_STORAGE_KEY)
  return stored ? JSON.parse(stored) : defaultShipmentData
}

export const setShipmentData = (data: ShipmentData): void => {
  localStorage.setItem(SHIPMENT_STORAGE_KEY, JSON.stringify(data))
}

export const resetShipmentData = (): void => {
  localStorage.removeItem(SHIPMENT_STORAGE_KEY)
}

// ETA Data
export const getETAData = (): ETAData => {
  const stored = localStorage.getItem(ETA_STORAGE_KEY)
  return stored ? JSON.parse(stored) : defaultETAData
}

export const setETAData = (data: ETAData): void => {
  localStorage.setItem(ETA_STORAGE_KEY, JSON.stringify(data))
}

export const resetETAData = (): void => {
  localStorage.removeItem(ETA_STORAGE_KEY)
}

// Reset all data
export const resetAllData = (): void => {
  resetDashboardMetrics()
  resetInventoryData()
  resetShipmentData()
  resetETAData()
}
