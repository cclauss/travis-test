env:PATH += ";C:\grr_deps\google-cloud-sdk\bin"

gcloud auth activate-service-account --key-file C:\grr_src\vagrant\windows\ogaro.appveyor-test.json

# Parse appveyor IS0 8601 commit date string into a Powershell DateTime object
$raw_commit_dt = [DateTime]$env:APPVEYOR_REPO_COMMIT_TIMESTAMP

$short_commit_dt = $raw_commit_dt.ToString("yyyy-MM-ddTHH:mmUTC")

$GCE_DEST = "gs://ogaro-travis-test/$short_commit_dt_$env:APPVEYOR_REPO_COMMIT/appveyor_build_$env:APPVEYOR_BUILD_NUMBER_job_$env:APPVEYOR_JOB_NUMBER/"

:: echo Uploading templates to gs://ogaro-travis-test/%APPVEYOR_REPO_COMMIT_TIMESTAMP%_%APPVEYOR_REPO_COMMIT%/appveyor_%APPVEYOR_BUILD_ID%_%APPVEYOR_JOB_ID%/
echo Uploading templates to $GCE_DEST

::gsutil -m cp C:\grr_src\output\* %GCE_DEST%
gsutil -m cp C:\Python27-x64\python.exe $GCE_DEST
