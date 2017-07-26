rem See https://www.appveyor.com/docs/how-to/secure-files/
gcloud auth activate-service-account --key-file C:\grr_src\vagrant\windows\ogaro.appveyor-test.json.enc

echo Uploading templates to "gs://ogaro-travis-test/appveyor"

gsutil -m cp C:\grr_src\output\* "gs://ogaro-travis-test/appveyor"
