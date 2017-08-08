mkdir C:\Users\appveyor\.vagrant.d | Out-Null
echo @'
Vagrant::configure('2') do |config|
  config.vm.boot_timeout = 1020
end
'@ | Out-File -encoding UTF8 C:\Users\appveyor\.vagrant.d\Vagrantfile

mkdir C:\downloads | Out-Null
cd C:\downloads
Start-FileDownload "https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2.msi"
Start-Process -FilePath "msiexec.exe" -ArgumentList "/a vagrant_1.7.2.msi /qb TARGETDIR=C:\Vagrant-1.7.2" -Wait
Start-FileDownload "http://download.virtualbox.org/virtualbox/4.3.12/VirtualBox-4.3.12-93733-Win.exe"
Start-Process -FilePath "VirtualBox-4.3.12-93733-Win.exe" -ArgumentList "-silent -logging -msiparams INSTALLDIR=C:\VBox-4.3.12" -Wait
cd $env:APPVEYOR_BUILD_FOLDER

While ((Test-NetConnection google.com -Port 80 -InformationLevel Quiet) -ne "True") {
    echo "waiting for network..."
    Start-Sleep 1
}

$env:PATH += ';C:\Vagrant-1.7.2\HashiCorp\Vagrant\bin;C:\VBox-4.3.12'
vagrant -v
