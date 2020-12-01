{ stdenv, libudev, python3Packages, unzip, hwdata, nix, boost }:

stdenv.mkDerivation {
  name = "niudu-playground";
  src = builtins.fetchGit {
    url = "/home/eugene/Projects/niudu";
  };
  nativeBuildInputs = [ unzip python3Packages.wrapPython boost ];
  buildInputs = [ libudev python3Packages.pyside2 python3Packages.pydenticon
    python3Packages.dbus-python python3Packages.pyudev python3Packages.libvirt hwdata
  ];
  pythonPath = with python3Packages; [ pyside2 pydenticon dbus-python pyudev libvirt shiboken2 ];
  buildPhase = ''
    python -m compileall lib/python/site-packages
    g++ -I${nix.dev}/include/nix -shared -o lib/ctypes_friendly_wrapper.so -fPIC ${nix}/lib/libnixutil.so src/libnixutil_ctypes_friendly_wrapper.cc -std=c++1z
  '';
  installPhase = ''
    mkdir $out
    cp -R bin lib share $out
    ln -s ${hwdata}/share/hwdata/pci.ids $out/share/niudu-devices/hwdata/pci.ids
    ln -s ${hwdata}/share/hwdata/usb.ids $out/share/niudu-devices/hwdata/usb.ids
  '';
  postFixup = ''
    wrapPythonPrograms  
  '';
}
