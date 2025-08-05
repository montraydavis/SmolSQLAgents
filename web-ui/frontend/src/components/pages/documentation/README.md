# Documentation Page

A comprehensive database documentation viewer that displays all documented tables, relationships, and business purposes in an organized, searchable format with tabbed navigation and detailed modal views.

## Features

### 🎯 Core Functionality
- **Tabbed Navigation**: Separate tabs for Tables, Relationships, and All Documentation
- **Search & Filter**: Real-time search across all documentation content
- **Category Filtering**: Filter by tables, relationships, or view all documentation
- **Detailed Modal View**: Click any item to see comprehensive documentation details
- **Status Tracking**: Visual status badges for documentation completion
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 🔍 Search & Filtering
- **Text Search**: Search across business purposes, documentation text, table names, and relationship types
- **Category Filter**: Filter by type (Tables, Relationships, or All)
- **Clear Filters**: Reset all filters with one click
- **Real-time Filtering**: Results update as you type or change filters

### 📊 Data Sources
The page automatically combines multiple data sources:
1. **Documentation API**: `/api/documentation/summaries` - For documented items with business purposes
2. **Schema API**: `/api/schema` - For raw schema data as fallback
3. **Combined View**: Merges both sources for comprehensive coverage

### 🎨 Visual Design
- **Card-based Layout**: Each documented item displayed as an interactive card
- **Status Badges**: Color-coded status indicators (Complete, Pending, Failed)
- **Tab Navigation**: Clean tab interface for different content types
- **Hover Effects**: Cards lift and highlight on interaction
- **Modern UI**: Professional Bootstrap-based design with custom styling

### 📱 Responsive Features
- **Mobile-friendly**: Cards stack vertically on small screens
- **Touch-friendly**: Large touch targets for mobile interaction
- **Adaptive Layout**: Tabs and filters adapt to screen size
- **Optimized Typography**: Readable text at all screen sizes

## Usage

### Basic Navigation
1. **View Documentation**: All documented items are displayed in organized tabs
2. **Search**: Use the search box to find specific documentation
3. **Filter**: Use the category dropdown to filter by type
4. **Switch Tabs**: Click between Tables, Relationships, and All Documentation
5. **Details**: Click any documentation card to view detailed information
6. **Refresh**: Use the refresh button to reload documentation data

### Tab Navigation
- **Tables Tab**: Shows all documented tables with business purposes and schema info
- **Relationships Tab**: Shows all documented relationships with types and details
- **All Documentation Tab**: Shows everything in a unified view

### Documentation Cards
Each card shows:
- **Type Badge**: Indicates if it's a Table or Relationship
- **Status Badge**: Shows documentation completion status
- **Title**: Table name or relationship description
- **Description**: Business purpose or documentation preview
- **Metadata**: Column count, relationship type, or processing date

### Detailed Modal
Clicking a documentation card opens a detailed modal showing:
- **Business Purpose**: Full business purpose text
- **Documentation**: Complete documentation content
- **Schema Information**: For tables, shows column details
- **Relationship Details**: For relationships, shows source and target tables
- **Metadata**: Processing status, dates, and other information

## Data Structure

### Documentation Item Object
```javascript
{
  id: "unique_identifier",
  name: "table_name",
  type: "table" | "relationship",
  business_purpose: "Business purpose description",
  documentation: "Detailed documentation text",
  status: "completed" | "pending" | "failed",
  processed_at: "2024-01-01T00:00:00Z",
  column_count: 5,
  columns: [...],
  relationship_type: "Foreign Key",
  constrained_table: "source_table",
  referred_table: "target_table"
}
```

### API Endpoints
- **GET** `/api/documentation/summaries` - Get all documented items
- **GET** `/api/schema` - Get raw schema data as fallback

## Styling

The page uses custom CSS classes:
- `.documentation-page` - Main container
- `.documentation-card` - Individual documentation cards
- `.content-tabs` - Tab navigation container
- `.content-area` - Main content display area
- `.filters-section` - Search and filter controls

## Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **Mobile Browsers**: iOS Safari, Chrome Mobile
- **Responsive**: Works on all screen sizes
- **Accessibility**: Keyboard navigation and screen reader support

## Performance

- **Lazy Loading**: Data loaded on component mount
- **Efficient Filtering**: Real-time filtering without API calls
- **Optimized Rendering**: Only re-renders when data changes
- **Memory Efficient**: Minimal state management

## Error Handling

- **Network Errors**: Graceful fallback to empty state
- **Data Errors**: Handles malformed documentation data
- **Loading States**: Shows spinner during data loading
- **Empty States**: Helpful messages when no data is available

## Status Indicators

### Status Badges
- **Complete** (Green): Documentation has been fully processed
- **Pending** (Yellow): Documentation is queued for processing
- **Failed** (Red): Documentation processing encountered an error
- **Unknown** (Gray): Status information not available

### Type Badges
- **Table** (Blue): Database table documentation
- **Relationship** (Cyan): Foreign key relationship documentation

## Content Organization

### Tables Tab
- Shows all documented tables
- Displays business purposes and schema information
- Shows column counts and processing status
- Includes schema details in modal view

### Relationships Tab
- Shows all documented relationships
- Displays relationship types and descriptions
- Shows source and target table information
- Includes detailed relationship mapping

### All Documentation Tab
- Unified view of all documented items
- Mixed display of tables and relationships
- Shows processing dates and status
- Comprehensive search across all content 