set PATH=%PATH%;C:\grr_deps\google-cloud-sdk\bin

powershell gcloud auth activate-service-account --key-file C:\grr_src\vagrant\windows\ogaro.appveyor-test.json

:: TODO(ogaro): Sort.
set GCE_DEST "gs://ogaro-travis-test/%APPVEYOR_REPO_COMMIT%/appveyor_%APPVEYOR_BUILD_ID%_%APPVEYOR_JOB_ID%/"
echo Uploading templates to %GCE_DEST%

gsutil -m cp C:\grr_src\output\* %GCE_DEST%
