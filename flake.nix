{
  description = "nazarewk/reef-recruitment";

  inputs.omnibus.url = "github:gtrunsec/omnibus";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {omnibus, ...} @ inputs: let
    inherit (inputs.nixpkgs) lib;
    inherit (omnibus.flake.inputs) std climodSrc flake-parts;
    systems = [
      "x86_64-linux"
      "aarch64-linux"
      "aarch64-darwin"
    ];
    omnibusStd =
      (omnibus.pops.std {
        inputs.inputs = {
          inherit std;
        };
      })
      .exports
      .default;
  in
    flake-parts.lib.mkFlake {inherit inputs;} {
      inherit systems;
      imports = [omnibusStd.flakeModule];
      std.std = omnibusStd.mkDefaultStd {
        cellsFrom = ./cells;
        inherit systems;
        inputs =
          inputs
          // {
            projectRoot = ./.;
            inherit climodSrc;
          };
      };
      std.harvest = {
        devShells = [
          "dev"
          "shells"
        ];
        packages = [
          "dev"
          "packages"
        ];
      };
    };
}
