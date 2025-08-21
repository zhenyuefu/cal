# University Calendar System

This is a [Next.js](https://nextjs.org/) project for generating personalized university course calendars with support for multiple API implementations.

## Features

- **Dual API Support**: Choose between Go API (v2 - fast) or Python API (v1 - legacy)
- **Course Filtering**: Filter courses by major, semester, and group
- **iCal Generation**: Generate calendar feeds compatible with all major calendar applications
- **Real-time Updates**: Calendar data is regularly updated from university sources
- **Responsive UI**: Modern React interface with Mantine components

## API Implementations

### Go API v2 (Recommended)
- **Location**: `/api/v2/cal.go`
- **Performance**: High-performance with sub-100ms response times
- **Features**: Advanced caching, comprehensive error handling, CORS support
- **Documentation**: See [Go API Implementation Guide](./GO_API_IMPLEMENTATION.md)

### Python API v1 (Legacy)
- **Location**: `/api/gen.py`, `/api/gens2.py`, `/api/gens3.py`
- **Compatibility**: Maintained for backward compatibility
- **Features**: Full feature parity with original implementation

## Getting Started

### Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### API Endpoints

- **Calendar Generation**: `/api/v2/cal?MAJ={major}&{UE}={group}`
- **Health Check**: `/api/v2/health`
- **Legacy APIs**: `/api/gen`, `/api/gens2`, `/api/gens3`

### Example Usage

Generate a calendar for DAC major with specific courses:
```
https://your-domain.com/api/v2/cal?MAJ=DAC&LRC=2&MLBDA=1&SEMESTER=s1
```

## Architecture

- **Frontend**: Next.js with React and Mantine UI
- **Backend**: Dual API (Go + Python) for calendar processing
- **Data**: Pre-processed JSON indexes for optimal performance
- **Deployment**: Vercel serverless functions
- **Caching**: Multi-level caching for performance optimization

## Supported Majors

- **AND**: Androide
- **DAC**: Data Analysis and Computing
- **IMA**: Image Processing
- **STL**: Software Technology and Languages
- **SAR**: Systems and Networks
- **SESI**: Embedded Systems
- **SFPN**: Foundations and Parallel Programming
- **BIM**: Bioinformatics

## Learn More

- [Go API Documentation](./api/v2/README.md)
- [Go Implementation Guide](./GO_API_IMPLEMENTATION.md)
- [Next.js Documentation](https://nextjs.org/docs)

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

The project includes proper Vercel configuration in `vercel.json` for both Go and Python APIs.
