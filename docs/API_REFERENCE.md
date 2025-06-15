# API Reference

## POST /analyze
> Analyze a public Git repository.

Request JSON | Type | Example
-------------|------|--------
`repo_url`   | string (URL) | `https://github.com/psf/requests`

### Response 200 (application/json)

Key | Type | Description
----|------|------------
`intro` | string | “Static analysis of X”
`grade` | string | A+++, A, B… F
`score` | int    | 1-100
`kwh`   | object | users → kWh / day
`hardware` | object | Typical CPU/GPU/RAM
`bullets` | string[] | Top warnings
`pdf_url` | string\|null | Relative path to report

### Errors
Code | Meaning
-----|--------
`400` | Invalid URL / payload  
`500` | Analysis failed (check detail)
