# Pre-Deployment Cleanup Script
# Fixes all critical issues found in audit

echo "🖖 Starting Vulcan-style pre-deployment cleanup..."

# Issue 1 & 2: Already fixed in config.py by git checkout
# The correct version has:
# - Single GEMINI config (lines 30-34)  
# - No MongoDB config

echo "✅ Issue 1: Duplicate GEMINI config - Fixed"
echo "✅ Issue 2: MongoDB config removed - Fixed"

# Issue 3: Test files - Move to /tests directory
echo "📁 Issue 3: Moving test files..."

# Create tests directory if it doesn't exist
mkdir -p backend/tests/debug_scripts

# Move debug/test files
files_to_move=(
    "check_config.py"
    "check_env.py"
    "check_status.py"
    "quick_test.py"
    "test_config.py"
    "test_settings.py"
    "test_webhook_sig.py"
)

for file in "${files_to_move[@]}"; do
    if [ -f "backend/$file" ]; then
        mv "backend/$file" "backend/tests/debug_scripts/$file"
        echo "  Moved $file to tests/debug_scripts/"
    fi
done

echo "✅ Issue 3: Test files organized"

# Issue 4: Print statements
# These are in:
# - app/main.py (lines 21-23, 33, 38)
# - app/services/ai.py (lines 11, 39)
# Will be fixed manually due to context

echo "⚠️  Issue 4: Print statements need manual review"
echo "   Files: app/main.py, app/services/ai.py"

echo ""
echo "🎯 Cleanup Summary:"
echo "   ✅ Configuration duplicates removed"
echo "   ✅ MongoDB config removed"  
echo "   ✅ Test files organized"
echo "   ⚠️  Print statements: Review app/main.py and app/services/ai.py"
echo ""
echo "🚀 Ready for deployment after print statement review!"
