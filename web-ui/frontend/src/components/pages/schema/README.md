# Schema Page

A comprehensive database schema viewer that displays all database tables, columns, data types, constraints, and relationships in an organized and visual format with statistics, search capabilities, and detailed modal views.

## Features

### 🎯 Core Functionality
- **Schema Overview**: Complete database schema visualization with statistics
- **Dual View Modes**: Card view and table view for different preferences
- **Search & Filter**: Real-time search across tables, columns, and data types
- **Sorting Options**: Sort by name, column count, or relationship count
- **Detailed Modal View**: Click any table to see comprehensive schema details
- **Statistics Dashboard**: Visual statistics cards showing database metrics
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 📊 Statistics Dashboard
- **Total Tables**: Count of all database tables
- **Total Columns**: Count of all columns across all tables
- **Total Relationships**: Count of foreign key relationships
- **Primary Keys**: Count of primary key constraints
- **Visual Cards**: Color-coded statistics with icons and hover effects

### 🔍 Search & Filtering
- **Text Search**: Search across table names, column names, and data types
- **Sort Options**: Sort by table name, column count, or relationship count
- **View Modes**: Switch between card view and table view
- **Real-time Filtering**: Results update as you type or change options

### 🎨 Visual Design
- **Card-based Layout**: Each table displayed as an interactive card
- **Data Type Colors**: Color-coded badges for different data types
- **Constraint Badges**: Visual indicators for PK, FK, UQ, NN constraints
- **Statistics Cards**: Hover effects and modern styling
- **Professional UI**: Clean Bootstrap-based design with custom styling

### 📱 Responsive Features
- **Mobile-friendly**: Cards stack vertically on small screens
- **Touch-friendly**: Large touch targets for mobile interaction
- **Adaptive Layout**: Statistics and controls adapt to screen size
- **Optimized Typography**: Readable text at all screen sizes

## Usage

### Basic Navigation
1. **View Schema**: All database tables are displayed with statistics
2. **Search**: Use the search box to find specific tables or columns
3. **Sort**: Use the dropdown to sort tables by different criteria
4. **Switch Views**: Toggle between card view and table view
5. **Details**: Click any table card or row to view detailed schema
6. **Refresh**: Use the refresh button to reload schema data

### View Modes
- **Card View**: Visual cards showing table information with column previews
- **Table View**: Compact table format with all tables listed in rows

### Schema Cards
Each card shows:
- **Table Name**: Primary identifier for the table
- **Column Count**: Number of columns in the table
- **Column Preview**: First 3 columns with data types and constraints
- **Relationship Count**: Number of relationships involving this table
- **Interactive**: Click to view detailed schema information

### Detailed Modal
Clicking a table opens a detailed modal showing:
- **Complete Column List**: All columns with data types and constraints
- **Table Statistics**: Summary of primary keys, foreign keys, etc.
- **Relationships**: All relationships involving this table
- **Metadata**: Detailed information about the table structure

## Data Structure

### Schema Data Object
```javascript
{
  tables: [
    {
      name: "table_name",
      columns: [
        {
          name: "column_name",
          type: "VARCHAR(255)",
          nullable: true,
          primary_key: false,
          foreign_key: false,
          unique: false,
          default: null
        }
      ]
    }
  ],
  relationships: [
    {
      constrained_table: "source_table",
      referred_table: "target_table",
      constrained_columns: ["column1"],
      referred_columns: ["column2"],
      relationship_type: "Foreign Key"
    }
  ],
  statistics: {
    totalTables: 10,
    totalColumns: 50,
    totalRelationships: 5,
    constraints: {
      primaryKeys: 10,
      foreignKeys: 5,
      uniqueConstraints: 3,
      notNullColumns: 25
    }
  }
}
```

### API Endpoints
- **GET** `/api/schema` - Get complete database schema information

## Styling

The page uses custom CSS classes:
- `.schema-page` - Main container
- `.stat-card` - Statistics dashboard cards
- `.schema-card` - Individual table schema cards
- `.controls-section` - Search and filter controls
- `.schema-content` - Main content display area

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
- **Data Errors**: Handles malformed schema data
- **Loading States**: Shows spinner during data loading
- **Empty States**: Helpful messages when no data is available

## Data Type Colors

### Color Coding
- **INTEGER**: Blue (Primary)
- **VARCHAR**: Cyan (Info)
- **DECIMAL**: Green (Success)
- **DATETIME**: Yellow (Warning)
- **DATE**: Gray (Secondary)
- **BOOLEAN**: Dark (Dark)

### Constraint Badges
- **PK**: Primary Key (Yellow)
- **FK**: Foreign Key (Cyan)
- **UQ**: Unique Constraint (Green)
- **NN**: Not Null (Red)

## Content Organization

### Statistics Dashboard
- **Visual Cards**: Color-coded statistics with icons
- **Hover Effects**: Cards lift and highlight on interaction
- **Real-time Updates**: Statistics update when data changes

### Card View
- **Table Cards**: Each table as an interactive card
- **Column Preview**: Shows first 3 columns with types
- **Relationship Info**: Shows relationship count
- **Hover Effects**: Cards lift and highlight on interaction

### Table View
- **Compact Format**: All tables in a single table
- **Sortable Columns**: Click headers to sort
- **Action Buttons**: View details for each table
- **Responsive**: Adapts to screen size

### Detailed Modal
- **Complete Schema**: All columns with full details
- **Statistics Panel**: Table-level statistics
- **Relationships Panel**: All related tables
- **Responsive Layout**: Adapts to modal size

## Search Capabilities

### Search Targets
- **Table Names**: Search by table name
- **Column Names**: Search by column name
- **Data Types**: Search by data type
- **Real-time**: Results update as you type

### Sort Options
- **Name**: Alphabetical by table name
- **Columns**: By number of columns (descending)
- **Relationships**: By number of relationships (descending)

## View Modes

### Card View
- **Visual**: Each table as a card with preview
- **Interactive**: Click cards for details
- **Responsive**: Cards stack on mobile
- **Preview**: Shows column types and constraints

### Table View
- **Compact**: All tables in tabular format
- **Sortable**: Click headers to sort
- **Actions**: View button for each table
- **Overview**: Quick comparison of tables

## Statistics Calculation

### Real-time Statistics
- **Table Count**: Total number of tables
- **Column Count**: Total number of columns
- **Relationship Count**: Total foreign key relationships
- **Constraint Counts**: Primary keys, foreign keys, etc.

### Data Type Analysis
- **Type Distribution**: Count of each data type
- **Constraint Analysis**: Count of each constraint type
- **Relationship Mapping**: Count of relationships per table 