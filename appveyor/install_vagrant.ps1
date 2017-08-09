$deps_dir = 'C:\grr_deps'
$vbox_url = 'http://download.virtualbox.org/virtualbox/5.1.26/VirtualBox-5.1.26-117224-Win.exe'
$vagrant_url = 'https://releases.hashicorp.com/vagrant/1.9.6/vagrant_1.9.6_x86_64.msi'
$vbox_download_path = '{0}\VirtualBox-5.1.26-117224-Win.exe' -f $deps_dir
$vagrant_download_path = '{0}\vagrant_1.9.6_x86_64.msi' -f $deps_dir
$vbox_install_dir = 'C:\VirtualBox-5.1.26'
$vagrant_install_dir = 'C:\Vagrant-1.9.6'

if (![System.IO.Directory]::Exists($deps_dir)) {
  mkdir $deps_dir | Out-Null
}

if ([System.IO.File]::Exists($vbox_download_path)) {
  Write-Output 'Using cached virtualbox installer.'
} else {
  Write-Output 'Downloading virtualbox..'
  (New-Object System.Net.WebClient).DownloadFile($vbox_url, $vbox_download_path)
}

if ([System.IO.File]::Exists($vagrant_download_path)) {
  Write-Output 'Using cached vagrant installer.'
} else {
  Write-Output 'Downloading vagrant..'
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  (New-Object System.Net.WebClient).DownloadFile($vagrant_url, $vagrant_download_path)
}

# Extract the vbox installers (32-bit and 64-bit) from the exe.
#Invoke-Expression "$vbox_download_path --silent --extract --logging --path $deps_dir"

Start-Process -FilePath $vbox_download_path -ArgumentList "-silent -logging -msiparams INSTALLDIR=$vbox_install_dir" -Wait
#$vbox_installer = Get-ChildItem -Path "$deps_dir\VirtualBox-*_amd64.msi" -Name
#Start-Process -Wait -FilePath "msiexec.exe" -ArgumentList "/a $deps_dir\$vbox_installer /quiet"
Start-Process -FilePath "msiexec.exe" -ArgumentList "/a $vagrant_download_path /qb TARGETDIR=$vagrant_install_dir" -Wait

[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";$vbox_install_dir;$vagrant_install_dir\HashiCorp\Vagrant\bin;",
    [EnvironmentVariableTarget]::Machine)

$env:Path += ";$vbox_install_dir;$vagrant_install_dir\HashiCorp\Vagrant\bin"

mkdir C:\Users\appveyor\.vagrant.d | Out-Null
echo @'
Vagrant::configure('2') do |config|
  config.vm.boot_timeout = 1020
end
'@ | Out-File -encoding UTF8 C:\Users\appveyor\.vagrant.d\Vagrantfile

vagrant up
ssh vagrant@127.0.0.1 -p 2222 -i .vagrant\machines\default\virtualbox\private_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -vvv -C "pwd"
vagrant ssh -c "uname -a"
