# Go API v2

A high-performance Go-based API for filtering and generating calendar feeds for university courses.

## Features

- **Fast Performance**: Uses pre-built JSON indexes for quick filtering
- **Caching**: In-memory caching with TTL for optimal performance  
- **CORS Support**: Enables cross-origin requests for development
- **Proper iCal Format**: Generates standards-compliant iCal files
- **Health Check**: Built-in health monitoring endpoint
- **Error Handling**: Comprehensive error handling and logging

## API Endpoints

### Calendar Filter

`GET /api/v2/cal`

**Parameters:**
- `MAJ` (required): Major/parcours code (e.g., "DAC", "IMA", "AND")
- `SEMESTER` (optional): Semester code ("s1", "s2", "s3") - s3 means M2
- `{UE_CODE}` (optional): UE codes with group numbers (e.g., "LRC=2", "MLBDA=1")

**Example:**
```
GET /api/v2/cal?MAJ=DAC&LRC=2&MLBDA=1&SEMESTER=s1
```

### Health Check

`GET /api/v2/health`

Returns API health status in JSON format.

## Supported Course Codes

### S1 (M1 First Semester)
- MOGPL, IL, LRC, MLBDA, MAPSI, BIMA, COMPLEX, MODEL, PPAR, ALGAV, DLP, OUV

### S2 (M1 Second Semester)  
- DJ, FoSyMa, IHM, RP, RA, RITAL, ML, IAMSI, SAM, IG3D

### S3 (M2)
- MU5IN250-MU5IN259, MU5IN852-MU5IN868, MU5IN650-MU5IN656, OIP, XAI

## Response Format

Returns an iCal file (.ics format) that can be imported into calendar applications.

**Headers:**
- `Content-Type: text/calendar; charset=utf-8`
- `X-Events-Count: {number}` - Number of events returned
- `Cache-Control: s-maxage=3600, stale-while-revalidate=86400`

## Development

### Local Testing

```bash
cd api/v2
go run test_go_api.go
```

### Build

```bash
cd api/v2
go build .
```

### Deploy

The API is automatically deployed to Vercel when pushed to the main branch.

## Cache Behavior

- JSON index files are cached for 1 hour
- Events are deduplicated based on time and summary
- HTTP cache headers set for 1 hour with stale-while-revalidate

## Filtering Logic

1. Maps UE codes to their respective parcours
2. Determines year level (M1/M2) based on UE codes
3. Loads relevant calendar data from JSON indexes
4. Filters events by:
   - UE code presence in event summary
   - Group number matching (if specified)
   - Excludes English courses
5. Sorts events chronologically
6. Generates iCal output

## Error Handling

- Returns 400 for missing MAJ parameter
- Logs file loading errors but continues processing
- Gracefully handles missing index files
- CORS preflight support for OPTIONS requests