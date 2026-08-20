#!/bin/bash
# VLSC Portal — Deploy unified landing page to www.vlsc.net
# Deploys to the DocumentRoot (/var/www/vlsc.net/)

set -e

# Configuration
LOCAL_PORTAL_DIR="/Users/cheenle/HAM/website/portal"
REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_WEBROOT="/var/www/vlsc.net"
BACKUP_DIR="/var/www/backups/landing_$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "VLSC Portal Deployment"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if local directory exists
if [ ! -d "$LOCAL_PORTAL_DIR" ]; then
    echo -e "${RED}Error: Local portal directory not found: $LOCAL_PORTAL_DIR${NC}"
    exit 1
fi

echo "Local directory: $LOCAL_PORTAL_DIR"
echo "Remote host: $REMOTE_HOST"
echo "Remote path: $REMOTE_WEBROOT (DocumentRoot)"
echo ""

cd "$LOCAL_PORTAL_DIR"

# Verify required files exist
echo "Checking required files..."
REQUIRED_FILES=(
    "index.html"
    "zh/index.html"
    "css/octen.css"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Required file missing: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} $file"
done

echo ""
echo "All files present."
echo ""

# Create deployment package
echo "Creating deployment package..."
DEPLOY_PACKAGE="/tmp/vlsc_landing_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$DEPLOY_PACKAGE" --exclude='deploy.sh' --exclude='.DS_Store' -C "$LOCAL_PORTAL_DIR" .
echo -e "${GREEN}✓${NC} Package created: $DEPLOY_PACKAGE"
echo ""

# Deploy to remote server
echo "Deploying to remote server..."
echo "This will:"
echo "  1. Create backup of current landing page"
echo "  2. Upload new files to DocumentRoot"
echo "  3. Set correct permissions"
echo "  4. Reload nginx"
echo ""

read -p "Continue with deployment? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Deployment cancelled."
    rm "$DEPLOY_PACKAGE"
    exit 0
fi

# SSH: backup and prep
ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
    set -e

    echo "Creating backup..."
    if [ -d "$REMOTE_WEBROOT" ] && [ "$(ls -A $REMOTE_WEBROOT 2>/dev/null)" ]; then
        sudo mkdir -p /var/www/backups
        sudo cp -r "$REMOTE_WEBROOT" "$BACKUP_DIR"
        echo "Backup created: $BACKUP_DIR"
    else
        echo "Webroot empty or doesn't exist — skipping backup"
    fi

    echo "Ensuring webroot exists..."
    sudo mkdir -p "$REMOTE_WEBROOT"

    echo "Setting ownership..."
    sudo chown -R www-data:www-data "$REMOTE_WEBROOT"
    sudo chmod -R 755 "$REMOTE_WEBROOT"
EOF

# Upload files
echo "Uploading files..."
scp "$DEPLOY_PACKAGE" "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Extract and finalize on remote
ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
    set -e

    echo "Extracting files..."
    cd "$REMOTE_WEBROOT"
    sudo tar -xzf "$DEPLOY_PACKAGE" --overwrite

    echo "Setting ownership..."
    sudo chown -R www-data:www-data "$REMOTE_WEBROOT"
    sudo chmod -R 755 "$REMOTE_WEBROOT"

    # Set correct permissions for files
    find "$REMOTE_WEBROOT" -type f -name "*.html" -exec sudo chmod 644 {} \;
    find "$REMOTE_WEBROOT" -type f -name "*.css" -exec sudo chmod 644 {} \;
    find "$REMOTE_WEBROOT" -type f -name "*.js" -exec sudo chmod 644 {} \; 2>/dev/null || true

    # Clean up
    rm -f "$DEPLOY_PACKAGE"

    echo "Testing nginx configuration..."
    sudo nginx -t || true

    echo "Reloading nginx..."
    sudo systemctl reload nginx || true

    echo ""
    echo "Portal deployment completed successfully!"
    echo "Landing page URL: https://$REMOTE_HOST/"
    echo "Backup location: $BACKUP_DIR"
EOF

# Clean up local package
rm -f "$DEPLOY_PACKAGE"

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Landing page deployed to: https://$REMOTE_HOST/"
echo ""
echo "To verify:"
echo "  1. Visit https://$REMOTE_HOST/"
echo "  2. Check all project cards link correctly"
echo "  3. Test language switching"
echo ""
echo "If you need to rollback:"
echo "  ssh $REMOTE_USER@$REMOTE_HOST"
echo "  sudo rm -rf $REMOTE_WEBROOT/*"
echo "  sudo cp -r $BACKUP_DIR/* $REMOTE_WEBROOT/"
echo ""
