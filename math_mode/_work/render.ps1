param(
    [string]$PdfPath,
    [string]$OutDir
)
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]

try {
    $fs = [System.IO.File]::OpenRead($PdfPath)
    $ras = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($fs)
    $pdf = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromStreamAsync($ras)) ([Windows.Data.Pdf.PdfDocument])
    Write-Host "pages: $($pdf.PageCount)"
} catch {
    Write-Host "LOAD FAILED: $($_.Exception.ToString())"
    exit 1
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

for ($i = 0; $i -lt $pdf.PageCount; $i++) {
    $page = $pdf.GetPage($i)
    $opts = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $opts.DestinationWidth = [uint32]2200
    $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $action = $page.RenderToStreamAsync($stream, $opts)
    $asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
    })[0]
    $task = $asTaskAction.Invoke($null, @($action))
    $task.Wait(-1) | Out-Null
    $outFile = Join-Path $OutDir ("page{0:D2}.png" -f ($i + 1))
    $netStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream.GetInputStreamAt(0))
    $out = [System.IO.File]::Create($outFile)
    $netStream.CopyTo($out)
    $out.Close(); $netStream.Close(); $stream.Dispose(); $page.Dispose()
    Write-Host "wrote $outFile"
}
