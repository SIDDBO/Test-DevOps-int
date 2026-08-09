# Frontend - Task Management UI

## Overview

Simple, responsive HTML/CSS/JavaScript UI for task management running on Nginx.

## Features

- Single-page application (SPA)
- Real-time task updates
- Add, complete, and delete tasks
- Health check indicator
- Error handling and notifications
- Auto-refresh every 5 seconds
- Mobile-responsive design

## Local Development

### View HTML File

```bash
# Simply open in browser
open index.html

# Or serve via HTTP
python -m http.server 8000
# Visit http://localhost:8000
```

### Build Docker Image

```bash
# Build
docker build -t task-app-frontend:1.0.0 .

# Run
docker run -p 8080:80 task-app-frontend:1.0.0
# Visit http://localhost:8080
```

## API Integration

The frontend communicates with the backend API:

```javascript
const API_URL = window.location.origin;

// Get tasks
fetch(`${API_URL}/api/tasks`);

// Create task
fetch(`${API_URL}/api/tasks`, {
  method: 'POST',
  body: JSON.stringify({title: 'New task'}),
  headers: {'Content-Type': 'application/json'}
});
```

## Configuration

### Nginx

The `nginx.conf` file configures:
- Port 80 (HTTP)
- Static file serving from `/usr/share/nginx/html`
- API proxy to backend service
- Caching for static assets
- CORS headers

### Backend Connection

The frontend connects to the backend using relative URLs:
- `/api/tasks` - API endpoints
- `/health` - Health check
- `/metrics` - Metrics endpoint

## Features Explained

### Health Check
Shows connection status to backend:
- **Green**: Backend is responding
- **Red**: Backend is not reachable

### Task Operations
- **Add**: Create new task
- **Complete**: Mark task as done (✓ button)
- **Delete**: Remove task (🗑 button)

### Auto-refresh
Tasks are refreshed every 5 seconds from `/api/tasks` endpoint.

## Browser Compatibility

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- No external dependencies (pure HTML/CSS/JS)
- Minimal data transfer
- Lazy loading of tasks
- Client-side error handling
- Connection pooling via fetch API

## Styling

- Gradient background
- Card-based layout
- Responsive grid (mobile-first)
- Smooth transitions
- Hover effects

## Error Handling

- Network errors show user-friendly messages
- 3-second error notification timeout
- Graceful degradation
- Automatic retry on refresh

## Accessibility

- Semantic HTML
- Clear labels
- Keyboard navigation
- Color contrast compliance
- Screen reader friendly

## Troubleshooting

### "Backend is not responding"
- Check backend service is running
- Verify Nginx proxy configuration
- Check security group rules
- Verify network connectivity

### Tasks not loading
- Check browser console for errors
- Verify `/api/tasks` endpoint works
- Check CORS headers in nginx.conf
- Review backend logs

### Styling not applied
- Clear browser cache
- Check CSS file location
- Verify Nginx is serving static files
- Check file permissions

### Form not submitting
- Check backend is accepting POST requests
- Verify Content-Type header
- Check CORS configuration
- Review error messages in console
