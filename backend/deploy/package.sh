#!/bin/bash
# Package Lambda functions for deployment

set -e

echo "Packaging Lambda functions..."

# Create deployment directory
mkdir -p dist

# Package Orchestrator Lambda
echo "Packaging Orchestrator Lambda..."
cd lambdas/orchestrator
zip -r ../../dist/orchestrator.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

# Package Agent Lambdas
echo "Packaging Agent Lambdas..."
for agent in business_profiling campaign_strategy content_generation scheduling_intelligence; do
    cd lambdas/agents
    zip -r ../../dist/${agent}.zip ${agent}.py __init__.py -x "*.pyc" -x "__pycache__/*"
    cd ../..
done

# Package Worker Lambdas
echo "Packaging Worker Lambdas..."
for worker in publishing_worker analytics_collector performance_learning; do
    cd lambdas/workers
    zip -r ../../dist/${worker}.zip ${worker}.py __init__.py -x "*.pyc" -x "__pycache__/*"
    cd ../..
done

# Add shared code to each package
echo "Adding shared code to packages..."
for package in dist/*.zip; do
    zip -ur $package shared/ -x "*.pyc" -x "__pycache__/*" -x "*/__pycache__/*"
    zip -ur $package repositories/ -x "*.pyc" -x "__pycache__/*" -x "*/__pycache__/*"
done

echo "Lambda functions packaged successfully in dist/"
ls -lh dist/
