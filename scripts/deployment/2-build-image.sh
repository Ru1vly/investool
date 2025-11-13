#!/bin/bash
# ============================================================================
# Phase 2.2: Build Production Docker Image
#
# Builds the production-ready Docker image with C++ engine + Python AI.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       FinRisk AI - Build Production Image                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
DEFAULT_REGISTRY="your-registry"
DEFAULT_IMAGE_NAME="finrisk-ai"
DEFAULT_VERSION="1.0.0"

echo "This script will build the production Docker image."
echo ""
echo "The image includes:"
echo "  • C++ InvestTool engine (compiled from source)"
echo "  • Python AI core with all dependencies"
echo "  • FastAPI REST API"
echo "  • Phase 5 fine-tuning capabilities"
echo ""

# Get registry information
read -p "Container registry (e.g., docker.io/username, gcr.io/project): " REGISTRY
REGISTRY=${REGISTRY:-$DEFAULT_REGISTRY}

read -p "Image name [$DEFAULT_IMAGE_NAME]: " IMAGE_NAME
IMAGE_NAME=${IMAGE_NAME:-$DEFAULT_IMAGE_NAME}

read -p "Version tag [$DEFAULT_VERSION]: " VERSION
VERSION=${VERSION:-$DEFAULT_VERSION}

FULL_IMAGE="$REGISTRY/$IMAGE_NAME:$VERSION"
LATEST_IMAGE="$REGISTRY/$IMAGE_NAME:latest"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Build Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Registry: $REGISTRY"
echo "  Image name: $IMAGE_NAME"
echo "  Version: $VERSION"
echo ""
echo "  Full image tag: $FULL_IMAGE"
echo "  Latest tag: $LATEST_IMAGE"
echo ""

read -p "Proceed with build? (y/n): " PROCEED
if [ "$PROCEED" != "y" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 1: Pre-build Checks"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "   Install from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker found: $(docker --version)"

# Check Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Dockerfile not found"
    echo "   Run this script from the project root directory"
    exit 1
fi
echo "✅ Dockerfile found"

# Check source files exist
if [ ! -f "bindings.cpp" ] || [ ! -f "CMakeLists.txt" ]; then
    echo "❌ Error: C++ source files not found"
    exit 1
fi
echo "✅ C++ source files found"

if [ ! -d "finrisk_ai" ]; then
    echo "❌ Error: finrisk_ai Python package not found"
    exit 1
fi
echo "✅ Python package found"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 2: Build Docker Image"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Starting multi-stage build..."
echo "  Stage 1: C++ compilation (may take 5-10 minutes)"
echo "  Stage 2: Python application setup"
echo ""

BUILD_START=$(date +%s)

# Build with progress
docker build \
    --tag "$FULL_IMAGE" \
    --tag "$LATEST_IMAGE" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg VERSION="$VERSION" \
    .

BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))

echo ""
echo "✅ Build completed in ${BUILD_TIME}s"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 3: Verify Image"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check image was created
if docker images | grep -q "$IMAGE_NAME.*$VERSION"; then
    echo "✅ Image created successfully"
    docker images | grep "$IMAGE_NAME" | head -3
else
    echo "❌ Error: Image not found after build"
    exit 1
fi

echo ""
echo "Image size: $(docker images --format "{{.Size}}" "$FULL_IMAGE")"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 4: Test Image (Optional)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

read -p "Test image locally before pushing? (y/n): " TEST
if [ "$TEST" = "y" ]; then
    echo ""
    echo "Starting test container..."

    # Run container with test environment
    CONTAINER_ID=$(docker run -d \
        --name finrisk-test \
        -p 8888:8000 \
        -e GEMINI_API_KEY="test_key" \
        "$FULL_IMAGE")

    echo "✅ Container started: $CONTAINER_ID"
    echo ""
    echo "Waiting for startup (10 seconds)..."
    sleep 10

    # Check if container is still running
    if docker ps | grep -q "$CONTAINER_ID"; then
        echo "✅ Container is running"

        # Check logs
        echo ""
        echo "Container logs:"
        docker logs "$CONTAINER_ID" 2>&1 | tail -20

        # Try health check
        echo ""
        echo "Testing health endpoint..."
        if curl -s http://localhost:8888/health > /dev/null 2>&1; then
            echo "✅ Health endpoint responds"
        else
            echo "⚠️  Health endpoint not responding (expected if no GEMINI_API_KEY)"
        fi
    else
        echo "❌ Container stopped unexpectedly"
        echo ""
        echo "Container logs:"
        docker logs "$CONTAINER_ID" 2>&1
    fi

    # Cleanup
    echo ""
    read -p "Stop and remove test container? (y/n): " CLEANUP
    if [ "$CLEANUP" = "y" ]; then
        docker stop "$CONTAINER_ID" > /dev/null 2>&1 || true
        docker rm "$CONTAINER_ID" > /dev/null 2>&1 || true
        echo "✅ Test container removed"
    else
        echo "ℹ️  Test container still running on http://localhost:8888"
        echo "   Stop with: docker stop $CONTAINER_ID && docker rm $CONTAINER_ID"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 5: Push to Registry"
echo "═══════════════════════════════════════════════════════════════"
echo ""

read -p "Push image to registry now? (y/n): " PUSH
if [ "$PUSH" = "y" ]; then
    echo ""
    echo "Pushing images..."
    echo "  $FULL_IMAGE"
    echo "  $LATEST_IMAGE"
    echo ""

    # Check if logged in to registry
    echo "Checking registry authentication..."
    if [[ "$REGISTRY" == *"gcr.io"* ]]; then
        echo "ℹ️  For GCR, ensure you're authenticated:"
        echo "   gcloud auth configure-docker"
    elif [[ "$REGISTRY" == *"docker.io"* ]] || [[ "$REGISTRY" == *"hub.docker.com"* ]]; then
        echo "ℹ️  For Docker Hub, ensure you're logged in:"
        echo "   docker login"
    fi

    echo ""
    read -p "Continue with push? (y/n): " CONFIRM_PUSH
    if [ "$CONFIRM_PUSH" = "y" ]; then
        docker push "$FULL_IMAGE"
        docker push "$LATEST_IMAGE"
        echo "✅ Images pushed successfully"
    else
        echo "⚠️  Push cancelled"
    fi
else
    echo "ℹ️  Skipping push. Push manually with:"
    echo "   docker push $FULL_IMAGE"
    echo "   docker push $LATEST_IMAGE"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Build Process Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Image details:"
echo "  Full tag: $FULL_IMAGE"
echo "  Latest tag: $LATEST_IMAGE"
echo ""
echo "Next steps:"
echo "  1. Update k8s/kustomization.yaml with your image:"
echo "     images:"
echo "       - name: finrisk-ai"
echo "         newName: $REGISTRY/$IMAGE_NAME"
echo "         newTag: \"$VERSION\""
echo ""
echo "  2. Run deployment script:"
echo "     ./scripts/deployment/3-deploy-k8s.sh"
echo ""

# Save build info
cat > build-info.txt << EOF
Build completed: $(date)
Image: $FULL_IMAGE
Latest: $LATEST_IMAGE
Build time: ${BUILD_TIME}s
EOF

echo "Build info saved to: build-info.txt"
echo ""
