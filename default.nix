{ stdenv, libudev, python3Packages, unzip, hwdata }:

#stdenv.mkDerivation {
python3Packages.buildPythonApplication rec {
  version = "0.1";
  pname = "niudu-playground";
  src = ./latest.zip;
  sourceRoot = ".";
  nativeBuildInputs = [ unzip ];
  buildInputs = [ libudev python3Packages.pyside2 python3Packages.pydenticon
    python3Packages.dbus-python python3Packages.pyudev python3Packages.libvirt hwdata
  ];
  pythonPath = with python3Packages; [ pyside2 pydenticon dbus-python pyudev libvirt shiboken2 ];
  installPhase = ''
    runHook preInstall
    mkdir -p "$out/lib/${python3Packages.python.libPrefix}/site-packages"
    export PYTHONPATH="$out/lib/${python3Packages.python.libPrefix}/site-packages:$PYTHONPATH"
    ${python3Packages.python}/bin/${python3Packages.python.executable} setup.py install \
      --install-lib=$out/lib/${python3Packages.python.libPrefix}/site-packages \
      --prefix="$out"
    eapth="$out/lib/${python3Packages.python.libPrefix}"/site-packages/easy-install.pth
    if [ -e "$eapth" ]; then
        # move colliding easy_install.pth to specifically named one
        mv "$eapth" $(dirname "$eapth")/${pname}-${version}.pth
    fi
    rm -f "$out/lib/${python3Packages.python.libPrefix}"/site-packages/site.py*
    #ln -s ${hwdata}/share/hwdata/pnp.ids $out/lib/${python3Packages.python.libPrefix}/site-packages/niudu_devices/subsystems/pnp.ids
    #ln -s ${hwdata}/share/hwdata/pci.ids $out/lib/${python3Packages.python.libPrefix}/site-packages/niudu_devices/subsystems/pci.ids
    #ln -s ${hwdata}/share/hwdata/usb.ids $out/lib/${python3Packages.python.libPrefix}/site-packages/niudu_devices/subsystems/usb.ids
    ln -s ${hwdata}/share/hwdata/pci.ids $out/share/niudu-devices/hwdata/pci.ids
    ln -s ${hwdata}/share/hwdata/usb.ids $out/share/niudu-devices/hwdata/usb.ids
    echo "data_path='$out/share/niudu-devices'" > "$out/lib/${python3Packages.python.libPrefix}"/site-packages/niudu_devices/static.py
    runHook postInstall
  '';
}
