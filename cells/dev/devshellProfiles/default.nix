{
  pkgs,
  lib,
  cell,
  ...
}: {
  env = [
    {
      name = "XDG_CONFIG_DIRS";
      eval = "$PRJ_CONFIG_HOME:$XDG_CONFIG_DIRS";
    }
  ];
  packages =
    [
      cell.packages.url-shortener.devEnv

      (pkgs.writeShellApplication {
        name = "url-shortener";
        runtimeInputs = [
          cell.packages.url-shortener.devEnv
        ];
        text = ''
          ${cell.packages.url-shortener.devEnv}/bin/python "$PRJ_ROOT/url_shortener.py" "$@"
        '';
      })
      (pkgs.writeShellApplication {
        name = "url-shortener-release";
        runtimeInputs = with pkgs; [
          coreutils
          zip
          (with cell.packages.url-shortener; python.withPackages (pp: (mkPythonDeps requirementsFile pp) ++ [pp.pip-chill]))
        ];
        text = ''
          set -x

          out="$PRJ_ROOT"

          pip-chill --verbose --no-chill | sed 's/^# //g' >"$out/requirements.lock.txt"
        '';
      })
    ]
    ++ (with pkgs; [
      gnumake
      nix-output-monitor
    ]);

  devshell.startup.symlink-interpreter.text = ''
    for file in "${cell.packages.url-shortener.devEnv}/bin"/* ; do
      ln -sf "$file" "$PRJ_PATH/"
    done
  '';
}
