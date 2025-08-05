# Relationships Page

A comprehensive database relationships viewer that displays all foreign key relationships in the database with filtering, search, and detailed view capabilities.

## Features

### 🎯 Core Functionality
- **Visual Relationship Display**: Shows relationships as cards with clear table-to-table flow
- **Search & Filter**: Search by table names, relationship types, or documentation
- **Type Filtering**: Filter relationships by type (One-to-Many, Many-to-One, etc.)
- **Detailed Modal View**: Click any relationship to see detailed information
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 🔍 Search & Filtering
- **Text Search**: Search across table names, relationship types, and documentation
- **Type Filter**: Filter by relationship type (Foreign Key, One-to-Many, etc.)
- **Clear Filters**: Reset all filters with one click
- **Real-time Filtering**: Results update as you type or change filters

### 📊 Data Sources
The page automatically tries multiple data sources:
1. **Documentation API**: `/api/documentation/relationships` - For documented relationships
2. **Schema API**: `/api/schema` - For raw foreign key relationships
3. **Fallback**: Creates basic relationship objects if no data is available

### 🎨 Visual Design
- **Card-based Layout**: Each relationship displayed as an interactive card
- **Flow Visualization**: Clear arrows showing relationship direction
- **Hover Effects**: Cards lift and highlight on hover
- **Color-coded Types**: Different colors for different relationship types
- **Modern UI**: Clean, professional design with Bootstrap components

### 📱 Responsive Features
- **Mobile-friendly**: Cards stack vertically on small screens
- **Touch-friendly**: Large touch targets for mobile interaction
- **Adaptive Layout**: Filters and headers adapt to screen size
- **Optimized Typography**: Readable text at all screen sizes

## Usage

### Basic Navigation
1. **View Relationships**: All relationships are displayed in a grid layout
2. **Search**: Use the search box to find specific relationships
3. **Filter**: Use the type dropdown to filter by relationship type
4. **Details**: Click any relationship card to view detailed information
5. **Refresh**: Use the refresh button to reload relationship data

### Relationship Cards
Each card shows:
- **Relationship Type**: Badge showing the type of relationship
- **Source Table**: The table that contains the foreign key
- **Target Table**: The table being referenced
- **Columns**: The specific columns involved in the relationship
- **Documentation**: Brief description if available

### Detailed Modal
Clicking a relationship card opens a detailed modal showing:
- **Constrained Table**: Full details of the source table
- **Referred Table**: Full details of the target table
- **Relationship Type**: The type of relationship with color coding
- **Documentation**: Full documentation text if available

## Data Structure

### Relationship Object
```javascript
{
  id: "unique_identifier",
  constrained_table: "source_table_name",
  referred_table: "target_table_name",
  constrained_columns: ["column1", "column2"],
  referred_columns: ["column1", "column2"],
  relationship_type: "Foreign Key" | "One-to-Many" | "Many-to-One" | etc.,
  documentation: "Optional documentation text"
}
```

### API Endpoints
- **GET** `/api/documentation/relationships` - Get documented relationships
- **GET** `/api/schema` - Get raw schema data including relationships

## Styling

The page uses custom CSS classes:
- `.relationships-page` - Main container
- `.relationship-card` - Individual relationship cards
- `.relationship-flow` - Visual flow between tables
- `.table-info` - Table information display
- `.arrow-container` - Direction indicator

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
- **Data Errors**: Handles malformed relationship data
- **Loading States**: Shows spinner during data loading
- **Empty States**: Helpful messages when no data is available 