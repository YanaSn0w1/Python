$downloads = "$env:USERPROFILE\Downloads"
$filenamePattern = "*.mp4"
$text = "Good Night my Love... Check the reply... Thank me later!"

$captions = @(
    @{text="Good Night my Love";     start=0.5; end=3.2},
    @{text="Check the reply";        start=3.6; end=6.1},
    @{text="Thank me later!";        start=6.5; end=10}
)

$video = Get-ChildItem "$downloads\$filenamePattern" -File | Sort LastWriteTime -Descending | Select-Object -First 1
$output = "$downloads\edited_$($video.Name)"
$tempVoice = "$env:TEMP\voice.wav"

Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft Zira Desktop")
$s.SetOutputToWaveFile($tempVoice)
$s.Speak($text)
$s.Dispose()

# ===================== NEW: Check if video has audio =====================
$hasAudio = $false
try {
    $audioCheck = & ffprobe -v quiet -select_streams a -show_entries stream=codec_name -of default=nw=1:nk=1 "$($video.FullName)" 2>$null
    if ($audioCheck) { $hasAudio = $true }
} catch { }

# ===================== Build filter (handles silent videos) =====================
$filter = "[0:v]hflip,format=yuv420p[v0];"

if ($hasAudio) {
    $filter += "[0:a]volume=0.12[bg];[1:a][bg]amix=inputs=2:duration=longest:dropout_transition=2[a]"
} else {
    $filter += "[1:a]volume=1.0[a]"   # no original audio → just use the voice
}

$current = "v0"
$index = 1
foreach ($cap in $captions) {
    $safeText = $cap.text -replace "'", "\\'" -replace ":", "\\:"
    $draw = "drawtext=fontfile=C\\:/Windows/Fonts/arial.ttf:text='$safeText':fontcolor=white:fontsize=52:borderw=7:bordercolor=black:box=1:boxcolor=black@0.75:x=(w-text_w)/2:y=h-text_h-130:enable='between(t,$($cap.start),$($cap.end))'"
    $next = "v$index"
    $filter += ";[$current]$draw,format=yuv420p[$next]"
    $current = $next
    $index++
}

# ===================== Run FFmpeg =====================
ffmpeg -i "$($video.FullName)" -i "$tempVoice" -filter_complex "$filter" -map "[$current]" -map "[a]" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k "$output" -y

Write-Host "✅ Done! Saved to: $output" -ForegroundColor Green
