# Simple Nginx frontend server
FROM nginx:alpine

# Copy HTML file
COPY index.html /usr/share/nginx/html/index.html

# Copy nginx config template
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Expose port
EXPOSE 80

# Entrypoint script to substitute environment variables
RUN mkdir -p /docker-entrypoint.d && \
    echo '#!/bin/sh' > /docker-entrypoint.d/10-substitute-backend-host.sh && \
    echo 'set -e' >> /docker-entrypoint.d/10-substitute-backend-host.sh && \
    echo 'export BACKEND_HOST=${BACKEND_HOST:-backend.backend.svc.cluster.local}' >> /docker-entrypoint.d/10-substitute-backend-host.sh && \
    echo 'envsubst "'"'"'${BACKEND_HOST}'"'"'" < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.d/10-substitute-backend-host.sh && \
    echo 'echo "Backend hostname substituted: $BACKEND_HOST"' >> /docker-entrypoint.d/10-substitute-backend-host.sh && \
    chmod +x /docker-entrypoint.d/10-substitute-backend-host.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
