import React, { useState } from 'react'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Grid from '@mui/material/Grid'

type FilterConfig = {
  key: string
  label: string
  type: 'text' | 'select'
  options?: { label: string; value: string }[]
}

type Props = {
  filters: FilterConfig[]
  onFilterChange: (filters: Record<string, string>) => void
}

export default function FilterBar({ filters, onFilterChange }: Props) {
  const [filterValues, setFilterValues] = useState<Record<string, string>>(
    filters.reduce((acc, f) => ({ ...acc, [f.key]: '' }), {})
  )

  const handleChange = (key: string, value: string) => {
    const updated = { ...filterValues, [key]: value }
    setFilterValues(updated)
    onFilterChange(updated)
  }

  return (
    <Paper sx={{ p: 2, mb: 3 }} elevation={1}>
      <Grid container spacing={2}>
        {filters.map((filter) => (
          <Grid item xs={12} sm={6} md={3} key={filter.key}>
            {filter.type === 'text' ? (
              <TextField
                fullWidth
                size="small"
                label={filter.label}
                value={filterValues[filter.key]}
                onChange={(e) => handleChange(filter.key, e.target.value)}
              />
            ) : (
              <FormControl fullWidth size="small">
                <InputLabel>{filter.label}</InputLabel>
                <Select
                  value={filterValues[filter.key]}
                  onChange={(e) => handleChange(filter.key, e.target.value)}
                  label={filter.label}
                >
                  <MenuItem value="">All</MenuItem>
                  {filter.options?.map((opt) => (
                    <MenuItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Grid>
        ))}
      </Grid>
    </Paper>
  )
}
