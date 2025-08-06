markdown
# GitHub Integration Backend

A FastAPI-based backend service for GitHub OAuth integration and data synchronization with MongoDB.

## Features

- GitHub OAuth2 authentication
- Complete GitHub data synchronization (organizations, repositories, commits, pull requests, issues, users)
- Dynamic data querying with pagination, filtering, and sorting
- Global search across all GitHub collections
- Async/await architecture for high performance
- Comprehensive error handling and logging

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB with Motor (async driver)
- **OAuth**: GitHub OAuth2
- **API Client**: httpx for GitHub REST API v3
- **Authentication**: OAuth2 with callback flow

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB
- GitHub OAuth App

### 1. Setup GitHub OAuth App

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App with:
   - Application name: `GitHub Integration App`
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/auth/github/callback`
3. Note your Client ID and Client Secret

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/osamaaurangzeb/fastapi-github-oauth-integration.git
cd github_integration_api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=your_secret_key_here
```

### 4. Run the Application

```bash
# Start MongoDB (if not running)
mongod

# Run the FastAPI server
python -m src.server

# Or use uvicorn directly
uvicorn src.server:app --reload --host localhost --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

### Authentication Endpoints

#### GET /auth/github/login
Redirects to GitHub OAuth authorization page.

**Response**: Redirect to GitHub

#### GET /auth/github/callback?code={code}
Handles GitHub OAuth callback and exchanges code for access token.

**Parameters**:
- `code` (query): OAuth authorization code from GitHub

**Response**:
```json
{
  "message": "GitHub integration successful",
  "user": {
    "id": 12345,
    "username": "octocat",
    "email": "octocat@github.com"
  }
}
```

### Integration Management

#### GET /integration/status?user_id={user_id}
Check integration status for a user.

**Response**:
```json
{
  "status": "active",
  "username": "octocat",
  "connected_at": "2024-01-01T12:00:00Z",
  "last_sync": "2024-01-02T12:00:00Z"
}
```

#### POST /integration/remove?user_id={user_id}
Delete integration data from MongoDB.

#### POST /integration/resync?user_id={user_id}
Re-fetch all GitHub data and re-store.

### Dynamic Data API

#### GET /data/{collection}
Query any GitHub collection with advanced filtering.

**Path Parameters**:
- `collection`: One of `github_organizations`, `github_repos`, `github_commits`, `github_pulls`, `github_issues`, `github_changelogs`, `github_users`

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `sort_by` (string): Field name to sort by
- `sort_order` (string): `asc` or `desc` (default: desc)
- `filter` (JSON string): Filters to apply
- `search` (string): Keyword search across relevant fields

**Examples**:
```bash
# Get repositories with pagination
GET /data/github_repos?page=1&limit=10

# Search commits by message
GET /data/github_commits?search=fix bug

# Filter pull requests by state
GET /data/github_pulls?filter={"state":"open"}

# Sort issues by creation date
GET /data/github_issues?sort_by=created_at&sort_order=asc
```

### Global Search

#### GET /data/?q={keyword}
Search across all GitHub collections.

**Query Parameters**:
- `q` (string): Search keyword
- `limit` (int): Max results per collection (default: 50)

**Response**:
```json
{
  "query": "bug fix",
  "results": {
    "repositories": [...],
    "commits": [...],
    "pull_requests": [...],
    "issues": [...]
  }
}
```

## Database Collections

The system creates the following MongoDB collections:

- `github_integration`: User OAuth tokens and integration status
- `github_organizations`: User organizations
- `github_repos`: Repositories (user + organization repos)
- `github_commits`: Repository commits
- `github_pulls`: Pull requests
- `github_issues`: Issues
- `github_changelogs`: Issue events/changelog
- `github_users`: Organization members and contributors

## Development

### Project Structure
```
github_integration_api/
├── src/
│   ├── controllers/         # Business logic
│   │   ├── auth_controller.py
│   │   ├── integration_controller.py
│   │   ├── sync_controller.py
│   │   └── data_controller.py
│   ├── routes/             # API routes
│   │   ├── auth_routes.py
│   │   ├── integration_routes.py
│   │   └── data_routes.py
│   ├── models/             # Pydantic models
│   │   └── github_models.py
│   ├── helpers/            # Utilities
│   │   ├── database.py
│   │   └── github_client.py
│   ├── config.py           # Configuration
│   └── server.py           # FastAPI app
├── requirements.txt
├── .env.example
└── README.md
```

### Testing

Create a test GitHub organization with:
- 3+ repositories
- 2000+ commits across repos
- 5+ pull requests
- 5+ issues

### Error Handling

The API includes comprehensive error handling with proper HTTP status codes and descriptive error messages.

## Deployment

For production deployment:

1. Set appropriate CORS origins
2. Use environment variables for all secrets
3. Configure MongoDB with authentication
4. Use a production WSGI server like Gunicorn
5. Set up proper logging and monitoring

## License

MIT License
