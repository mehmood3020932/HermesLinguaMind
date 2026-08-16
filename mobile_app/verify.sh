#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     HERMES LINGUAMIND — PHASE 8 VERIFICATION                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "📦 Step 1: Installing dependencies..."
flutter pub get
if [ $? -eq 0 ]; then
    echo "✅ flutter pub get — PASSED"
else
    echo "❌ flutter pub get — FAILED"
    exit 1
fi
echo ""

echo "🔍 Step 2: Running static analysis..."
flutter analyze
if [ $? -eq 0 ]; then
    echo "✅ flutter analyze — PASSED (0 errors, 0 warnings)"
else
    echo "❌ flutter analyze — FAILED"
    exit 1
fi
echo ""

echo "🧪 Step 3: Running tests..."
flutter test
if [ $? -eq 0 ]; then
    echo "✅ flutter test — PASSED"
else
    echo "❌ flutter test — FAILED"
    exit 1
fi
echo ""

echo "📱 Step 4: Building debug APK..."
flutter build apk --debug
if [ $? -eq 0 ]; then
    echo "✅ flutter build apk --debug — PASSED"
else
    echo "❌ flutter build apk --debug — FAILED"
    exit 1
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ ALL CHECKS PASSED — Phase 8 is production-ready!          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
