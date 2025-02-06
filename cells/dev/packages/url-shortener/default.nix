{
  pkgs,
  lib,
  __inputs__,
  ...
}: let
  mkScript = import ./mkPythonScript.nix {inherit pkgs lib;};
in
  mkScript rec {
    name = "url-shortener";
    imageName = "pw/${name}";
    python = pkgs.python313;
    src = __inputs__.inputs.projectRoot;
    scriptFile = src + /url_shortener.py;
    makeWrapperArgs = [
      "--prefix NIX_PYTHONPATH : ${src}"
    ];
    imageEnv.LISTEN_ADDRESS = "0.0.0.0";
  }
