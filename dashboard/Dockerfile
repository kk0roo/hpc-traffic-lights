# Minimal static-site container for the optional dashboard.
# Build:  docker build -t hpc-traffic-lights-dashboard dashboard/
# Run:    docker run --rm -p 8080:80 hpc-traffic-lights-dashboard
# Then open http://localhost:8080
FROM httpd:2.4

# httpd serves files from /usr/local/apache2/htdocs/ by default.
COPY index.html /usr/local/apache2/htdocs/index.html

# (Optional, future) copy generated plots into the document root:
# COPY ../results/plots/ /usr/local/apache2/htdocs/plots/
