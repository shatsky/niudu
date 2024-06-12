{ stdenv, systemd, python3Packages, unzip, hwdata, nix, boost, nlohmann_json }:

stdenv.mkDerivation {
  name = "niudu-playground";
  src = builtins.fetchGit {
    url = ./.;
  };
  nativeBuildInputs = [ unzip python3Packages.wrapPython boost ];
  buildInputs = [ systemd python3Packages.pyside6 python3Packages.pydenticon
    python3Packages.dbus-python python3Packages.pyudev python3Packages.libvirt hwdata
  ];
  pythonPath = with python3Packages; [ pyside6 pydenticon dbus-python pyudev libvirt shiboken6 ];
  buildPhase = ''
    python -m compileall lib/python/site-packages
    ln -s ${hwdata}/share/hwdata/pci.ids share/niudu-devices/hwdata/pci.ids
    ln -s ${hwdata}/share/hwdata/usb.ids share/niudu-devices/hwdata/usb.ids
  '';
  installPhase = ''
    mkdir $out
    cp -R bin lib share $out
  '';
  postFixup = ''
    wrapPythonPrograms  
  '';
}
