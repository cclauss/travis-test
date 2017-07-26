$env:PATH += ";C:\grr_deps\google-cloud-sdk\bin"

gcloud auth activate-service-account --key-file C:\grr_src\vagrant\windows\ogaro.appveyor-test.json

# Parse appveyor IS0 8601 commit date string (e.g 2017-07-26T16:49:31.0000000Z)
# into a Powershell DateTime object
$raw_commit_dt = [DateTime]$env:APPVEYOR_REPO_COMMIT_TIMESTAMP

# Create a shorter, more readable time string.
$short_commit_dt = $raw_commit_dt.ToString("yyyy-MM-ddTHH:mmUTC")

$GCE_DEST = "gs://ogaro-travis-test/{0}_{1}/appveyor_build_{2}_job_{3}/" -f $short_commit_dt, $env:APPVEYOR_REPO_COMMIT, $env:APPVEYOR_BUILD_NUMBER, $env:APPVEYOR_JOB_NUMBER

echo "Uploading templates to {0}" -f $GCE_DEST

gsutil -m cp "C:\Python27-x64\python.exe" $GCE_DEST
