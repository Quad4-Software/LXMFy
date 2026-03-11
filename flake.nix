{
  description = "LXMFy - A bot framework for creating LXMF bots on the Reticulum Network";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        rns = pkgs.python3Packages.buildPythonPackage rec {
          pname = "rns";
          version = "1.1.3";
          format = "pyproject";

          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            hash = "sha256-5wZnp2f+Ujurjn6gYnRHJYxOZ2O3dW+7pQxlVtu4Q5k=";
          };

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            cryptography
            pyserial
            netifaces
          ];

          doCheck = false;
        };

        lxmf = pkgs.python3Packages.buildPythonPackage rec {
          pname = "lxmf";
          version = "0.9.3";
          format = "pyproject";

          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            hash = "sha256-0000000000000000000000000000000000000000000000000000000000000000";
          };

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            rns
          ];

          doCheck = false;
        };

        lxmfy = pkgs.python3Packages.buildPythonPackage rec {
          pname = "lxmfy";
          version = "1.6.1";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with pkgs.python3Packages; [
            poetry-core
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            lxmf
            rns
          ];

          doCheck = false;
        };

        pythonWithLxmfy = pkgs.python3.withPackages (ps: with ps; [
          lxmfy
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [ 
            pkgs.python3
            pkgs.poetry
          ];

          shellHook = ''
            echo "LXMFy development environment"
            echo "Python: $(python3 --version)"
            echo "Poetry is available for dependency management"
            echo "Run: poetry install --with dev"
            echo "Run: task --list"
          '';
        };

        packages.default = lxmfy;

        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "lxmfy" ''
            exec ${pythonWithLxmfy}/bin/python -m lxmfy.cli "$@"
          ''}/bin/lxmfy";
        };
      }
    );
}

