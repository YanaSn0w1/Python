$downloads = "$env:USERPROFILE\Downloads"
$filenamePattern = "*.mp4"
$text = "Good Morning Builders... Say it back... Whos grinding rn?"

$captions = @(
    @{text="Good Morning Builders";     start=0.5; end=3.2},
    @{text="Say it back";               start=3.6; end=6.1},
    @{text="Whos grinding rn?";    start=6.5; end=10}
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

$filter = "[0:v]hflip,format=yuv420p[v0];[0:a]volume=0.12[bg];[1:a][bg]amix=inputs=2:duration=longest:dropout_transition=2[a]"
$current = "v0"
$index = 1
foreach ($cap in $captions) {
    $safeText = $cap.text -replace "'", "\\'"
    $draw = "drawtext=fontfile=C\\:/Windows/Fonts/arial.ttf:text='$safeText':fontcolor=white:fontsize=52:borderw=7:bordercolor=black:box=1:boxcolor=black@0.75:x=(w-tw)/2:y=h-th-130:enable=between(t\,$($cap.start)\,$($cap.end))"
    $next = "v$index"
    $filter += ";[$current]$draw,format=yuv420p[$next]"
    $current = $next
    $index++
}

ffmpeg -i "$($video.FullName)" -i "$tempVoice" -filter_complex "$filter" -map "[$current]" -map "[a]" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k "$output" -y
