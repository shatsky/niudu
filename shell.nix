let
 #pkgs_unstable = import <nixos-unstable> {};
 pkgs = import <nixpkgs> {};
 pkgs_unstable = pkgs;
in
pkgs.stdenv.mkDerivation {
  name = "niudu-playground";
  buildInputs = [ pkgs.cmake pkgs.zlib pkgs.libGL pkgs.xorg.libxcb pkgs.libudev pkgs_unstable.python3Packages.pyside2 pkgs.python3Packages.pydenticon pkgs.boost pkgs.python3Packages.dbus-python pkgs.python3Packages.pyudev ];
  shellHook = ''
    export PYTHONPATH=$PYTHONPATH:${pkgs_unstable.python3Packages.pyside2}/lib/python3.7/site-packages:${pkgs_unstable.python3Packages.shiboken2}/lib/python3.7/site-packages
    export QT_PLUGIN_PATH="${pkgs_unstable.qt5.qtbase}/lib/qt-5.12.3/plugins"
    [ -f pci.ids ] || ln -s ${pkgs.hwdata}/share/hwdata/pci.ids pci.ids
    [ -f usb.ids ] || ln -s ${pkgs.hwdata}/share/hwdata/usb.ids usb.ids
    #[ -f pnp.ids ] || ln -s ${pkgs.hwdata}/share/hwdata/pnp.ids pnp.ids
    [ -f pnp.ids ] || curl "http://tim.id.au/pnp-ids/pnp.ids" > pnp.ids
    g++ -I${pkgs.nix.dev}/include/nix -shared -o niudu-nix/ctypes_friendly_wrapper.so -fPIC ${pkgs.nix}/lib/libnixutil.so niudu-nix/ctypes_friendly_wrapper.cc -std=c++1z
  '';
}
