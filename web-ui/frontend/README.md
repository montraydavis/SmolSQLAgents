# SQL Agent Frontend

A React-based web interface for the Smol-SQL Agents Suite, providing an intuitive way to interact with AI-powered SQL agents for database documentation, natural language query processing, and SQL generation.

## 🚀 Features

### Core Functionality
- **Natural Language Query Processing**: Convert plain English to SQL using AI agents
- **Database Documentation Explorer**: Browse and search database schema and relationships
- **SQL Generation & Validation**: Generate, validate, and execute SQL queries
- **Entity Recognition**: Identify relevant database entities for your queries
- **Business Context Analysis**: Understand business logic and domain concepts
- **Query Optimization**: Get performance suggestions and optimization tips

### User Interface
- **Splash Screen**: Application initialization with SQL Agent status checking
- **Top Navigation**: Switch between different application pages
- **Documentation Sidebar**: Explore database structure and relationships
- **Query Interface**: Natural language input with comprehensive results display
- **Modal Details**: Detailed information for selected database items

## 📁 Project Structure

```
src/
├── components/
│   ├── ui/                    # Basic UI components (SplashScreen, TopNavigation)
│   ├── query/                 # Query functionality components
│   │   ├── QueryPage.js       # Main query interface
│   │   ├── SQLAgentStatus.js  # Agent status display
│   │   ├── QueryInput.js      # Natural language input
│   │   ├── EntityRecognitionResults.js
│   │   ├── BusinessContext.js
│   │   ├── SQLGeneration.js   # Generated SQL display
│   │   ├── QueryResults.js    # Query execution results
│   │   └── OptimizationSuggestions.js
│   ├── documentation/         # Documentation components
│   │   ├── DocumentationSidebar.js
│   │   ├── ItemDetailsModal.js
│   │   └── DocumentationExplorer.js
│   ├── pages/                # Page components
│   │   ├── relationships/     # Relationships page
│   │   ├── documentation/    # Documentation page
│   │   └── schema/          # Schema page
│   └── documentation-explorer/ # Legacy folder (to be consolidated)
├── App.js                    # Main application component
├── App.css                   # Application styles
└── index.js                  # Application entry point
```

## 🛠️ Technology Stack

- **React 19.1.1**: Modern React with hooks and functional components
- **Bootstrap 5**: Responsive UI framework with Bootstrap Icons
- **Fetch API**: HTTP requests to backend SQL Agent services
- **CSS3**: Custom styling with responsive design

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Backend SQL Agent services running on `http://127.0.0.1:5000`

### Installation

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```

3. **Open Application**
   Navigate to [http://localhost:3000](http://localhost:3000) in your browser

### Available Scripts

- **`npm start`**: Runs the app in development mode
- **`npm test`**: Launches the test runner
- **`npm run build`**: Builds the app for production
- **`npm run eject`**: Ejects from Create React App (one-way operation)

## 🔧 Configuration

### Backend Connection

The frontend connects to the SQL Agent backend services. Ensure the backend is running and accessible at:

```
http://127.0.0.1:5000/api
```

### Environment Variables

Create a `.env` file in the project root for environment-specific configuration:

```env
REACT_APP_API_BASE_URL=http://127.0.0.1:5000/api
REACT_APP_POLLING_INTERVAL=1000
REACT_APP_MAX_POLLING_ATTEMPTS=30
```

## 📱 Application Flow

### 1. Initialization
- **Splash Screen**: Checks SQL Agent availability and initialization status
- **Status Polling**: Monitors backend connectivity with progress indicators
- **Agent Status**: Displays current SQL Agent status and capabilities

### 2. Main Interface
- **Top Navigation**: Switch between Query, Relationships, Schema, and Documentation pages
- **Documentation Sidebar**: Browse database structure with search capabilities
- **Query Interface**: Natural language input with comprehensive results

### 3. Query Processing
- **Natural Language Input**: Type queries in plain English
- **Entity Recognition**: Automatic identification of relevant database entities
- **Business Context**: Domain-specific analysis and concept matching
- **SQL Generation**: AI-powered SQL generation with validation
- **Query Execution**: Test generated SQL with sample data
- **Optimization**: Performance suggestions and improvements

## 🔍 API Integration

### Backend Endpoints

The frontend integrates with these backend endpoints:

- **`/api/status`**: Check SQL Agent availability and status
- **`/api/query`**: Process natural language queries and generate SQL
- **`/api/schema`**: Retrieve database schema information
- **`/api/documentation/summaries`**: Get documentation summaries
- **`/api/documentation/tables/{table}`**: Get detailed table documentation
- **`/api/documentation/relationships/{id}`**: Get relationship documentation
- **`/api/search`**: Search documentation using semantic search

### Error Handling

- **Connection Errors**: Graceful handling of backend connectivity issues
- **API Errors**: User-friendly error messages for failed requests
- **Timeout Handling**: Automatic retry mechanisms for transient failures
- **Fallback UI**: Degraded functionality when services are unavailable

## 🎨 UI Components

### Core Components

- **`SplashScreen`**: Application initialization with progress indicators
- **`TopNavigation`**: Main navigation between application pages
- **`DocumentationSidebar`**: Database structure browser with search
- **`QueryPage`**: Main query interface with comprehensive results
- **`ItemDetailsModal`**: Detailed information display for database items

### Query Components

- **`SQLAgentStatus`**: Real-time agent status and capabilities
- **`QueryInput`**: Natural language input with suggestions
- **`EntityRecognitionResults`**: Display of identified database entities
- **`BusinessContext`**: Business logic and domain analysis
- **`SQLGeneration`**: Generated SQL with validation status
- **`QueryResults`**: Query execution results and sample data
- **`OptimizationSuggestions`**: Performance and optimization tips

## 🔧 Development

### Component Architecture

The application follows a modular component architecture:

- **UI Components**: Reusable interface elements
- **Query Components**: Specialized components for query processing
- **Documentation Components**: Database exploration and documentation
- **Page Components**: Full-page layouts for different sections

### State Management

- **React Hooks**: `useState`, `useEffect`, `useCallback` for state management
- **Component Props**: Data flow through component hierarchy
- **Local Storage**: Persistence of user preferences and settings

### Styling

- **Bootstrap 5**: Responsive grid system and components
- **Custom CSS**: Application-specific styling and animations
- **Bootstrap Icons**: Consistent iconography throughout the interface

## 🚀 Deployment

### Production Build

```bash
npm run build
```

This creates a `build` folder with optimized production files.

### Deployment Options

- **Static Hosting**: Deploy to Netlify, Vercel, or similar services
- **Docker**: Containerize the application for consistent deployment
- **CDN**: Serve static assets through a content delivery network

### Environment Configuration

Configure the backend API URL for production:

```env
REACT_APP_API_BASE_URL=https://your-backend-domain.com/api
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style

- Follow React best practices
- Use functional components with hooks
- Maintain consistent component structure
- Add appropriate error handling
- Include meaningful comments

## 📚 Related Documentation

- [Backend API Documentation](../API_DOCUMENTATION.md)
- [SQL Agent Architecture](../../docs/concepts/architecture.md)
- [Agent Documentation](../../docs/agents/)
- [Database Integration](../../docs/database/)

## 🆘 Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Ensure the SQL Agent backend is running
   - Check the API base URL configuration
   - Verify network connectivity

2. **Component Loading Issues**
   - Clear browser cache
   - Restart the development server
   - Check for JavaScript console errors

3. **Query Processing Errors**
   - Verify backend agent availability
   - Check query syntax and format
   - Review backend logs for detailed errors

### Debug Mode

Enable debug logging by setting:

```env
REACT_APP_DEBUG=true
```

This will provide detailed console output for troubleshooting.

---

**Built with ❤️ for the Smol-SQL Agents Suite**
