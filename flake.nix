{
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        p2nix = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
      in
      with self.packages.${system};
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            poetry
            jq
            podman-compose
            swagger-cli
          ];
        };

        packages = {
          kpconn-exe = pkgs.writeScript "kpconn-runner" ''
            #!${pkgs.runtimeShell}
            ${kpconn-deps}/bin/gunicorn -w 4 "kpconn.server.app:create_app()" --bind 0.0.0.0:8000
          '';

          kpconn-deps = (p2nix.mkPoetryApplication {
            projectDir = ./.;
            python = pkgs.python311;
            overrides = p2nix.overrides.withDefaults (self: super: {
              sdfval = super.sdfval.overridePythonAttrs (old: {
                buildInputs = old.buildInputs or [ ] ++ [ pkgs.python311.pkgs.poetry-core ];
              });
            });
          }).dependencyEnv;

          kpconn-source = pkgs.stdenv.mkDerivation {
            src = ./kpconn;
            name = "kpconn-source";
            dontBuild = true;
            installPhase = ''
              mkdir -p $out/app
              cp -r . $out/app/kpconn
            '';
          };

          kpconn-docker =
            pkgs.dockerTools.streamLayeredImage {
              name = "kpconn";
              tag = "latest";
              contents = [
                pkgs.busybox
                kpconn-source
              ];
              config = {
                Cmd = [ kpconn-exe ];
                WorkingDir = "/app";
              };
            };
        };


      }
    );
}
