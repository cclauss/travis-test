$env:PATH += ";C:\grr_deps\google-cloud-sdk\bin"

gcloud auth activate-service-account --key-file C:\grr_src\vagrant\windows\ogaro.appveyor-test.json

if (!$?) {
  exit 1
}

# Parse appveyor IS0 8601 commit date string (e.g 2017-07-26T16:49:31.0000000Z)
# into a Powershell DateTime object
$raw_commit_dt = [DateTime]$env:APPVEYOR_REPO_COMMIT_TIMESTAMP

# Create a shorter, more readable time string.
$short_commit_timestamp = $raw_commit_dt.ToString("yyyy-MM-ddTHH:mmUTC")

$gce_dest = "gs://ogaro-travis-test/{0}_{1}/appveyor_build_{2}_job_{3}/" -f $short_commit_timestamp, $env:APPVEYOR_REPO_COMMIT, $env:APPVEYOR_BUILD_NUMBER, $env:APPVEYOR_JOB_NUMBER

echo "Uploading templates to $gce_dest"

$stop_watch = [Diagnostics.Stopwatch]::StartNew()
gsutil cp "C:\grr_src\output\*" $gce_dest
if (!$?) {
  exit 2
}
$stop_watch.Stop()
$upload_duration = $stop_watch.Elapsed.TotalSeconds

# gsutil will print an info message recommending using the -m option (parallel
# object upload) when copying objects to GCP. For some reason however, that
# doesn't seem to work properly on Appveyor. Some files arbitrarily fail to
# upload with unhelpful error messages like 'Duplicate type [0:0:2]'
echo "Sequential object upload took $upload_duration seconds"
