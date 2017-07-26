rem TODO(ogaro): Move this to the installation stage.
set PATH=%PATH%;C:\grr_deps\google-cloud-sdk\bin

rem See https://www.appveyor.com/docs/how-to/secure-files/
powershell gcloud auth activate-service-account --key-file C:\grr_src\vagrant\windows\ogaro.appveyor-test.json

echo Uploading templates to "gs://ogaro-travis-test/appveyor"

rem gsutil -m cp C:\grr_src\output\* "gs://ogaro-travis-test/appveyor"
powershell gsutil -m cp C:\Python27-x64\python.exe "gs://ogaro-travis-test/appveyor"
