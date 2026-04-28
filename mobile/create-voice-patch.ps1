# Script to patch @react-native-voice/voice for AndroidX compatibility
# This fixes the build.gradle file to use AndroidX instead of old support library

$buildGradlePath = "node_modules\@react-native-voice\voice\android\build.gradle"

Write-Host "Patching @react-native-voice/voice for AndroidX compatibility..." -ForegroundColor Cyan

# Read the file
$content = Get-Content $buildGradlePath -Raw

# Replace the old support library with AndroidX
$oldPattern = 'implementation "com.android.support:appcompat-v7:\${supportVersion}"'
$newDependency = 'implementation "androidx.appcompat:appcompat:1.6.1"'

if ($content -match 'com.android.support:appcompat-v7') {
    Write-Host "Found old support library dependency. Replacing with AndroidX..." -ForegroundColor Yellow
    $content = $content -replace 'implementation "com.android.support:appcompat-v7:\$\{supportVersion\}"', $newDependency
    Set-Content $buildGradlePath -Value $content -NoNewline
    Write-Host "Successfully patched build.gradle" -ForegroundColor Green
} else {
    Write-Host "Dependency already patched or not found" -ForegroundColor Magenta
}

Write-Host "`nGenerating patch file..." -ForegroundColor Cyan
npx patch-package @react-native-voice/voice

Write-Host "`nPatch created successfully!" -ForegroundColor Green
Write-Host "The patch will be automatically applied after 'npm install'" -ForegroundColor Cyan
