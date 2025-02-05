{
  inputs,
  cell,
}: let
  inherit (inputs.std) lib;
  inherit (inputs) std;
in {
  # Tool Homepage: https://numtide.github.io/devshell/
  default = lib.dev.mkShell {
    name = "nazarewk/url-shortener-tech-test devshell";

    imports =
      [
        std.std.devshellProfiles.default
      ]
      ++ builtins.attrValues cell.devshellProfiles;
  };
}
